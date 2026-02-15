from typing import List, Dict, Any
from backend.database import SessionLocal, MemoryEvent
from backend.memory.vector_store import store
from backend.utils.llm_client import call_embed
from backend.config import MAX_SEARCH_RESULTS


def search_memory(query: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        query_vector = call_embed(query, timeout_s=20)
        if not query_vector:
            return []

        # returns (event_uuid, L2_distance)
        results = store.search(query_vector, top_k=MAX_SEARCH_RESULTS * 2)

        candidates = []
        seen_ids = set()

        for event_id, distance in results:
            if event_id in seen_ids:
                continue
            seen_ids.add(event_id)

            event = session.query(MemoryEvent).filter(MemoryEvent.id == event_id).first()
            if not event:
                continue

            similarity = 1.0 / (1.0 + distance)

            candidates.append(
                {
                    "id": event.id,
                    "score": similarity,
                    "distance": distance,
                    "summary": event.summary_1line,
                    "text": event.raw_text,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                    "source_type": event.source_type,
                    "entities": event.entities,
                }
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:MAX_SEARCH_RESULTS]

    finally:
        session.close()
