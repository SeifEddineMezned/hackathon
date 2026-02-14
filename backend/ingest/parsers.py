import os
from typing import Dict, Any
from PyPDF2 import PdfReader
from backend.utils.llm_client import call_vlm
from backend.utils.whisper_client import transcribe_audio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading text {file_path}: {e}")
        return ""

def parse_pdf(file_path: str) -> str:
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            ctx = page.extract_text()
            if ctx:
                text += ctx + "\n"
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        return ""

def parse_image(file_path: str) -> Dict[str, Any]:
    """Returns {vision_caption: str, raw_text: str (OCR optional)}"""
    prompt = (
        "Analyze this image in detail. "
        "1. Describe the scene or content. "
        "2. Extract any visible text if significant. "
        "3. List key objects or people. "
        "4. Identify any actionable information (dates, tasks)."
    )
    caption = call_vlm(file_path, prompt)
    return {"vision_caption": caption, "raw_text": caption} # Treat caption as text for now

def parse_audio(file_path: str) -> str:
    return transcribe_audio(file_path)
