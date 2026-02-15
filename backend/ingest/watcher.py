import time
import logging
import os
import threading
from pathlib import Path
from queue import Queue, Empty

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from backend.config import WATCH_DIRS
from backend.ingest.processor import IngestionProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Single ingestion queue + single worker = no SQLite "database is locked"
INGEST_QUEUE: "Queue[tuple[str, str]]" = Queue()
STOP_EVENT = threading.Event()


def _detect_source_type(file_path: str) -> str | None:
    """
    Determine source type by which WATCH_DIR folder contains the file.
    Returns the type_name or None if not matched.
    """
    p_obj = Path(file_path).resolve()

    for type_name, folder_path in WATCH_DIRS.items():
        f_obj = Path(folder_path).resolve()
        try:
            p_obj.relative_to(f_obj)
            return type_name
        except ValueError:
            continue

    return None


def _wait_for_file_stability(path: str, timeout: float = 6.0, interval: float = 0.4) -> bool:
    """
    Wait until file size is stable (copy completed).
    Returns True if stable, False if timeout or missing.
    """
    start_time = time.time()
    last_size = -1

    while time.time() - start_time < timeout:
        try:
            if not os.path.exists(path):
                return False
            size = os.path.getsize(path)
            if size == last_size and size > 0:
                return True
            last_size = size
            time.sleep(interval)
        except OSError:
            time.sleep(interval)

    return False


def start_worker(processor: IngestionProcessor) -> None:
    """
    Start ONE background worker thread that processes queued ingestions sequentially.
    This eliminates SQLite database locks from concurrent writes.
    """
    def worker():
        logger.info("Ingestion worker started (single-threaded DB writes).")
        while not STOP_EVENT.is_set():
            try:
                path, source_type = INGEST_QUEUE.get(timeout=0.5)
            except Empty:
                continue

            try:
                # Ensure file is fully copied before processing
                if not _wait_for_file_stability(path):
                    logger.warning(f"File unstable or deleted, skipping: {path}")
                    continue

                logger.info(f"Worker processing ({source_type}): {path}")
                processor.process_file(path, source_type)

            except Exception as e:
                logger.exception(f"Worker error for {path}: {e}")
            finally:
                INGEST_QUEUE.task_done()

        logger.info("Ingestion worker stopped.")

    threading.Thread(target=worker, daemon=True).start()


class IngestHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_processed = {}  # path -> timestamp
        self.debounce_seconds = 2.0
        self.lock = threading.Lock()

    def _should_process(self, path: str) -> bool:
        filename = os.path.basename(path).lower()

        # Ignore temp/hidden/partial files
        if filename.startswith("~$") or filename.endswith(".tmp") or filename.startswith("."):
            return False

        now = time.time()
        with self.lock:
            last_time = self.last_processed.get(path, 0)
            if now - last_time < self.debounce_seconds:
                return False
            self.last_processed[path] = now

        return True

    def on_created(self, event):
        if event.is_directory:
            return
        self._handle_event(event.src_path, "created")

    def on_modified(self, event):
        if event.is_directory:
            return
        self._handle_event(event.src_path, "modified")

    def _handle_event(self, path: str, event_type: str) -> None:
        if not self._should_process(path):
            return

        source_type = _detect_source_type(path)
        if not source_type:
            return

        logger.info(f"File event ({event_type}): {path} -> queued as {source_type}")

        # IMPORTANT: enqueue only. Do NOT process in multiple threads.
        INGEST_QUEUE.put((path, source_type))


def start_watching():
    processor = IngestionProcessor()
    start_worker(processor)

    observer = Observer()

    for type_name, folder in WATCH_DIRS.items():
        p_obj = Path(folder)
        p_obj.mkdir(parents=True, exist_ok=True)

        logger.info(f"Watching {p_obj} for {type_name}")
        observer.schedule(IngestHandler(), str(p_obj), recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        STOP_EVENT.set()
        observer.stop()
    observer.join()


if __name__ == "__main__":
    start_watching()
