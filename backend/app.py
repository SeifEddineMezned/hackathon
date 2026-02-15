from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import threading
import logging
from datetime import datetime

from backend.database import init_db, SessionLocal, MemoryEvent, ActionItem
from backend.ingest.watcher import start_watching
from backend.retrieval.reasoning import ReasoningEngine
from backend.maintenance.jobs import job_runner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI MINDS API", version="1.0")

# Initialize DB
init_db()

# Start Watcher in background
try:
    watcher_thread = threading.Thread(target=start_watching, daemon=True)
    watcher_thread.start()
    logger.info("Background watcher started successfully.")
except Exception as e:
    logger.error(f"Failed to start background watcher: {e}")

# Start Maintenance Job
job_runner.start()

# Reasoning Engine
engine = ReasoningEngine()

class QueryRequest(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    answer: str
    confidence: int
    citations: List[str]
    intent: str
    uncertainty_flags: List[str]

@app.get("/status")
def get_status():
    return {"status": "running", "watcher": watcher_thread.is_alive()}

@app.post("/query", response_model=QueryResponse)
def query_endpoint(request: QueryRequest):
    try:
        result = engine.process_query(request.query)
        return QueryResponse(
            answer=result.get("answer", "I'm unsure."),
            confidence=int(result.get("confidence", 0)),
            citations=result.get("citations", []),
            intent=result.get("intent", "unknown"),
            uncertainty_flags=result.get("uncertainty_flags", [])
        )
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/timeline")
def get_timeline(limit: int = 50):
    session = SessionLocal()
    try:
        events = session.query(MemoryEvent).order_by(MemoryEvent.created_at.desc()).limit(limit).all()
        return [{
            "id": e.id,
            "created_at": e.created_at.isoformat() if e.created_at else None,
            "source_type": e.source_type,
            "summary": e.summary_1line,
            "topics": e.topics
        } for e in events]
    finally:
        session.close()

@app.get("/actions")
def get_actions(status: Optional[str] = None):
    session = SessionLocal()
    try:
        query = session.query(ActionItem)
        if status:
            query = query.filter(ActionItem.status == status)
        items = query.order_by(ActionItem.due_date.asc().nullslast()).all()
        return [{
            "id": i.id,
            "task": i.task,
            "owner": i.owner,
            "priority": i.priority,
            "status": i.status,
            "due_date": i.due_date.isoformat() if i.due_date else None
        } for i in items]
    finally:
        session.close()

if __name__ == "__main__":
    import uvicorn
    # Make sure we bind locally
    uvicorn.run(app, host="127.0.0.1", port=8000)
