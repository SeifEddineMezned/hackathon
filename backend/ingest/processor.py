import logging
import hashlib
import os
import time
from sqlalchemy.exc import IntegrityError

from backend.ingest.parsers import parse_text, parse_pdf, parse_image, parse_audio
from backend.utils.llm_client import call_llm, call_embed, clean_json_response
from backend.database import SessionLocal, MemoryEvent, ActionItem
from backend.memory.vector_store import store
from backend.config import MODEL_MAIN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IngestionProcessor:
    def __init__(self):
        pass  # stateless

    def process_file(self, file_path: str, source_type: str):
        session = SessionLocal()
        t0 = time.time()

        try:
            logger.info(f"Processing ({source_type}): {file_path}")

            if not os.path.exists(file_path):
                logger.warning(f"File vanished before processing: {file_path}")
                return

            # --------------------
            # STAGE 1: PARSE
            # --------------------
            logger.info("[STAGE] parse_start")
            content = ""
            vision_caption = None

            if source_type in ["text", "docs"]:
                if file_path.lower().endswith(".pdf"):
                    content = parse_pdf(file_path)
                else:
                    content = parse_text(file_path)

            elif source_type == "images":
                result = parse_image(file_path)
                content = result.get("raw_text", "") or ""
                vision_caption = result.get("vision_caption", "") or ""

            elif source_type == "audio":
                content = parse_audio(file_path)

            logger.info(
                f"[STAGE] parse_done chars={len(content)} cap_chars={len(vision_caption or '')} dt={time.time()-t0:.2f}s"
            )

            # If PDF has no extractable text, still store the event (demo-safe)
            if not content and not vision_caption:
                logger.warning(f"No content extracted from {file_path}. Storing minimal event anyway.")
                content = ""

            # --------------------
            # STAGE 2: DEDUPE HASH
            # --------------------
            raw_data = (content or "") + (vision_caption or "")
            content_hash = hashlib.sha256(raw_data.encode("utf-8", "ignore")).hexdigest()

            existing = session.query(MemoryEvent).filter_by(content_hash=content_hash).first()
            if existing:
                logger.info(f"Duplicate content found for {os.path.basename(file_path)}, skipping.")
                return

            # --------------------
            # STAGE 3: COMMIT MINIMAL EVENT FIRST (prevents “nothing happens”)
            # --------------------
            logger.info("[STAGE] db_insert_minimal_start")
            event = MemoryEvent(
                source_type=source_type,
                source_path=file_path,
                content_hash=content_hash,
                raw_text=content,
                vision_caption=vision_caption,
                summary_1line="(processing...)",
                summary_short="",
                entities=[],
                topics=[],
                intent_label="general",
                metadata_json={"status": "processing"},
            )
            session.add(event)
            session.commit()  # ✅ event now appears in Timeline immediately
            session.refresh(event)
            logger.info(f"[STAGE] db_insert_minimal_done event_id={event.id} dt={time.time()-t0:.2f}s")

            # --------------------
            # STAGE 4: METADATA EXTRACTION
            # --------------------
            logger.info("[STAGE] metadata_start")
            metadata = self._extract_metadata(content if content else (vision_caption or ""))
            logger.info(f"[STAGE] metadata_done dt={time.time()-t0:.2f}s")

            # Update event fields
            event.summary_1line = metadata.get("summary_1line", "No summary available.")
            event.summary_short = "\n".join(metadata.get("summary_bullets", []))
            event.entities = metadata.get("entities", [])
            event.topics = metadata.get("topics", [])
            event.intent_label = metadata.get("intent", "general")
            event.metadata_json = metadata

            # Replace placeholder with real content
            if not event.summary_short:
                event.summary_short = "- processed"

            # Create Action Items
            actions_added = 0
            for action in metadata.get("action_items", []):
                if isinstance(action, dict) and action.get("task"):
                    item = ActionItem(
                        task=action.get("task", "Unknown Task"),
                        owner=action.get("owner", "user"),
                        priority=action.get("priority", "medium"),
                        status="open",
                        evidence_event_id=event.id,
                    )
                    session.add(item)
                    actions_added += 1

            # --------------------
            # STAGE 5: EMBEDDINGS
            # --------------------
            logger.info("[STAGE] embed_start")
            text_to_embed = f"{event.summary_1line}\n{event.summary_short}\n{(content or '')[:800]}"
            vector = call_embed(text_to_embed, timeout_s=20)
            logger.info(f"[STAGE] embed_done ok={vector is not None} dt={time.time()-t0:.2f}s")

            if vector:
                internal_id = store.add_event(event.id, vector)
                if internal_id is not None:
                    event.embedding_ref = str(internal_id)
            else:
                logger.warning("Embedding generation failed; continuing without embedding_ref.")

            # --------------------
            # STAGE 6: FINAL COMMIT
            # --------------------
            logger.info("[STAGE] commit_final_start")
            session.commit()
            logger.info(
                f"Successfully ingrained event {event.id} with {actions_added} actions. total={time.time()-t0:.2f}s"
            )

        except Exception as e:
            logger.exception(f"Error processing {file_path}: {e}")
            session.rollback()

            # If event exists and we crashed after minimal commit, mark it
            try:
                if "event" in locals() and event and event.id:
                    event.metadata_json = {"status": "failed", "error": str(e)}
                    event.summary_1line = "(failed processing)"
                    session.commit()
            except Exception:
                session.rollback()

        finally:
            session.close()

    def _extract_metadata(self, text: str) -> dict:
        if not text:
            return {
                "summary_1line": "Empty content",
                "summary_bullets": ["No extractable text found."],
                "entities": [],
                "topics": [],
                "action_items": [],
                "intent": "general",
            }

        prompt = f"""
Analyze this content and extract structured data in strict JSON.
Content:
{text[:3000]}

Return ONLY a valid JSON object with these keys:
- "summary_1line": string
- "summary_bullets": [string]
- "entities": [string]
- "topics": [string]
- "action_items": [ {{"task": string, "owner": string, "priority": "high|medium|low"}} ]
- "intent": string (informational|task|reminder)
"""

        for attempt in range(2):
            resp = call_llm(MODEL_MAIN, prompt, json_mode=True, timeout_s=60)
            data = clean_json_response(resp)
            if data and isinstance(data, dict) and "summary_1line" in data:
                # Normalize missing keys
                data.setdefault("summary_bullets", [])
                data.setdefault("entities", [])
                data.setdefault("topics", [])
                data.setdefault("action_items", [])
                data.setdefault("intent", "general")
                return data
            logger.warning(f"Invalid JSON from LLM, retrying... attempt={attempt+1}")

        return {
            "summary_1line": "Automatic processing result",
            "summary_bullets": ["Content processed but metadata extraction unclear."],
            "entities": [],
            "topics": [],
            "action_items": [],
            "intent": "general",
        }
