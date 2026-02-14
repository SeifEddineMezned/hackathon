import requests
import json
import subprocess
import base64
import logging
from typing import Dict, List, Optional, Any
from backend.config import OLLAMA_BASE_URL, MODEL_MAIN, MODEL_EMBEDDING, MODEL_VISION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def call_llm(model: str, prompt: str, system: Optional[str] = None, json_mode: bool = False) -> str:
    """Calls Ollama LLM endpoint."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096}
    }
    if system:
        payload["system"] = system
    if json_mode:
        payload["format"] = "json"

    try:
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling LLM {model}: {e}")
        return ""

def call_embed(text: str, model: str = MODEL_EMBEDDING) -> List[float]:
    """Generates embedding for text using Ollama."""
    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": model,
        "prompt": text
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        embedding = response.json().get("embedding")
        if not embedding:
            logger.warning(f"No embedding returned for text: {text[:50]}...")
            return []
        return embedding
    except requests.exceptions.RequestException as e:
        logger.error(f"Error generating embedding: {e}")
        return []

def call_vlm(image_path: str, prompt: str, model: str = MODEL_VISION) -> str:
    """Calls Vision Language Model on an image file."""
    url = f"{OLLAMA_BASE_URL}/api/generate"
    
    try:
        with open(image_path, "rb") as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode("utf-8")
            
        payload = {
            "model": model,
            "prompt": prompt,
            "images": [img_b64],
            "stream": False
        }
        
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        return response.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"Error calling VLM: {e}")
        return ""

def clean_json_response(response: str) -> Dict[str, Any]:
    """Extracts JSON from markdown fences if present."""
    try:
        start = response.find("```json")
        if start != -1:
            end = response.find("```", start + 7)
            if end != -1:
                json_str = response[start + 7:end].strip()
                return json.loads(json_str)
        
        start = response.find("{")
        end = response.rfind("}")
        if start != -1 and end != -1:
             return json.loads(response[start:end+1])
             
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON response")
        return {}
