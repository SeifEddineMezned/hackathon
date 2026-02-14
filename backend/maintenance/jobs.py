import time
import logging
import threading
from backend.database import SessionLocal, MemoryEvent
from backend.utils.llm_client import call_llm
from backend.config import MODEL_MAIN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenanceJob:
    def __init__(self, interval_minutes=60):
        self.interval = interval_minutes * 60
        self.running = False
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
    def _run_loop(self):
        logger.info("Starting maintenance job cycle...")
        while self.running:
            try:
                self._cluster_and_summarize()
            except Exception as e:
                logger.error(f"Maintenance job error: {e}")
            time.sleep(self.interval)
            
    def _cluster_and_summarize(self):
        # 1. Fetch recent un-summarized events (placeholder logic)
        session = SessionLocal()
        try:
            # Simple heuristic: find events from last hour
            # For hackathon demo, maybe just log that we are 'consolidating'
            logger.info("Running consolidation job: clustering recent memories...")
            
            # Real implementation would cluster vectors here
            # For now, just a dummy operation to show activity
            count = session.query(MemoryEvent).count()
            logger.info(f"Total memories available for clustering: {count}")
            
        finally:
            session.close()

# Singleton
job_runner = MaintenanceJob(interval_minutes=5) # Run every 5 mins for demo visibility
