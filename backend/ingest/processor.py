import logging
import hashlib
import json
import os
from datetime import datetime
from threading import Thread

from backend.ingest.parsers import parse_text, parse_pdf, parse_image, parse_audio
from backend.utils.llm_client import call_llm, call_embed, clean_json_response
from backend.database import SessionLocal, MemoryEvent, ActionItem, Entity, Topic, GraphEdge
from backend.memory.vector_store import store
from backend.config import MODEL_MAIN, MODEL_EMBEDDING

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngestionProcessor:
    def __init__(self):
        self.session = SessionLocal()

    def process_file(self, file_path: str, source_type: str):
        try:
            logger.info(f"Processing {source_type}: {file_path}")
            
            # 1. Parse content
            content = ""
            vision_caption = None
            
            if source_type in ["text", "docs"]:
                if file_path.endswith(".pdf"):
                    content = parse_pdf(file_path)
                else:
                    content = parse_text(file_path)
            elif source_type == "images":
                result = parse_image(file_path)
                content = result.get("raw_text", "")
                vision_caption = result.get("vision_caption", "")
            elif source_type == "audio":
                content = parse_audio(file_path)
                
            if not content and not vision_caption:
                logger.warning(f"No content extracted from {file_path}")
                return

            # Hash check for duplicates
            content_hash = hashlib.sha256((content + (vision_caption or "")).encode()).hexdigest()
            existing = self.session.query(MemoryEvent).filter_by(content_hash=content_hash).first()
            if existing:
                logger.info(f"Duplicate content found for {file_path}, skipping.")
                return

            # 2. Extract Metadata (Summary, Entities, Actions) using LLM
            metadata = self._extract_metadata(content)
            
            # 3. Create Memory Event
            event = MemoryEvent(
                source_type=source_type,
                source_path=file_path,
                content_hash=content_hash,
                raw_text=content,
                vision_caption=vision_caption,
                summary_1line=metadata.get("summary_1line", ""),
                summary_short="\n".join(metadata.get("summary_bullets", [])),
                entities=metadata.get("entities", []),
                topics=metadata.get("topics", []),
                intent_label=metadata.get("intent", "general"),
                metadata_json=metadata
            )
            
            self.session.add(event)
            self.session.flush() # Get ID
            
            # 4. Create Action Items
            for action in metadata.get("action_items", []):
                item = ActionItem(
                    task=action.get("task", ""),
                    owner=action.get("owner", "user"),
                    priority=action.get("priority", "medium"),
                    status="open",
                    evidence_event_id=event.id
                )
                self.session.add(item)
                
            # 5. Generate Embedding & Store
            text_to_embed = f"{event.summary_1line}\n{event.summary_short}\n{content[:500]}"
            vector = call_embed(text_to_embed)
            if vector:
                store.add_event(event.id, vector)
                event.embedding_ref = str(store.next_id - 1) # Or handle ID mapping logic inside store
            
            self.session.commit()
            logger.info(f"Successfully ingrained event {event.id}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            self.session.rollback()
        finally:
            self.session.close()

    def _extract_metadata(self, text: str) -> dict:
        prompt = f"""
        Analyze this text and extract structured data in JSON format regarding:
        1. A 1-line summary.
        2. A short bulleted summary (3-5 items).
        3. Key entities (people, organizations, places).
        4. Main topics/keywords.
        5. Action items (tasks with owner, priority).
        6. Intent (informational, request, task, etc).

        Text:
        {text[:2500]} 

        Return ONLY a valid JSON object with keys:
        - summary_1line
        - summary_bullets (list of strings)
        - entities (list of strings)
        - topics (list of strings)
        - action_items (list of objects with keys: task, owner, priority)
        - intent
        """
        response = call_llm(MODEL_MAIN, prompt, json_mode=True)
        return clean_json_response(response)
