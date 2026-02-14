import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from backend.config import WATCH_DIRS
from backend.ingest.processor import IngestionProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestHandler(FileSystemEventHandler):
    def __init__(self, processor):
        self.processor = processor

    def on_created(self, event):
        if event.is_directory:
            return
        logger.info(f"New file detected: {event.src_path}")
        self._process(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        # Debounce logic could be added here
        logger.info(f"File modified: {event.src_path}")
        self._process(event.src_path)

    def _process(self, path):
        # Determine source type based on folder
        for type_name, folder_path in WATCH_DIRS.items():
            if str(folder_path) in path:
                self.processor.process_file(path, type_name)
                break

def start_watching():
    processor = IngestionProcessor()
    observer = Observer()
    
    for type_name, path in WATCH_DIRS.items():
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            
        logger.info(f"Watching {path} for {type_name}")
        event_handler = IngestHandler(processor)
        observer.schedule(event_handler, str(path), recursive=True)

    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()
