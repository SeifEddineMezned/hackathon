from typing import List, Dict, Any
from backend.database import SessionLocal, MemoryEvent
from backend.memory.vector_store import store
from backend.utils.llm_client import call_embed
from backend.config import MAX_SEARCH_RESULTS

def search_memory(query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """
    Search for relevant memory events using vector similarity and metadata filtering.
    """
    session = SessionLocal()
    try:
        # 1. Generate query embedding
        query_vector = call_embed(query)
        if not query_vector:
            return []
            
        # 2. Retrieve top-k events from FAISS
        results = store.search(query_vector, top_k=MAX_SEARCH_RESULTS * 2) # Fetch more for filtering
        
        # 3. Filter and Rank
        candidates = []
        seen_ids = set()
        
        for event_id, score in results:
            if event_id in seen_ids:
                continue
            seen_ids.add(event_id)
            
            event = session.query(MemoryEvent).filter(MemoryEvent.id == event_id).first()
            if not event:
                continue
                
            # Apply filters (e.g. date range, entity match) if implemented
            # For now, just basic text relevance
            
            candidates.append({
                "id": event.id,
                "score": score,
                "summary": event.summary_1line,
                "text": event.raw_text,
                "created_at": event.created_at,
                "source_type": event.source_type,
                "entities": event.entities
            })
            
        # Re-rank based on keyword match? (Optional)
        # Simply return top K vectors for now
        return candidates[:MAX_SEARCH_RESULTS]
            
    finally:
        session.close()
