import json
import requests
import re
import base64
from typing import Any, Dict, List, Optional

from backend.config import OLLAMA_BASE_URL, MODEL_EMBEDDING, MODEL_VISION


def _strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def clean_json_response(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None

    text = _strip_code_fences(text)

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    try:
        return json.loads(text)
    except Exception:
        return None


def call_llm(model: str, prompt: str, json_mode: bool = False, timeout_s: int = 60) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"

    if json_mode:
        prompt = (
            "Return ONLY valid JSON. No prose. No markdown.\n"
            "If unsure, return {}.\n\n"
            + prompt
        )

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.2 if json_mode else 0.4},
    }

    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return r.json().get("response", "")


def call_embed(text: str, model: str = MODEL_EMBEDDING, timeout_s: int = 20) -> Optional[List[float]]:
    if not text:
        return None

    url = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": model, "prompt": text}

    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return r.json().get("embedding")


def call_vlm(image_path: str, prompt: str, timeout_s: int = 60) -> str:
    """
    Calls Ollama Vision model (e.g., qwen2.5vl:3b).
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"

    with open(image_path, "rb") as f:
        image_base64 = base64.b64encode(f.read()).decode("utf-8")

    payload = {
        "model": MODEL_VISION,
        "prompt": prompt,
        "images": [image_base64],
        "stream": False,
    }

    r = requests.post(url, json=payload, timeout=timeout_s)
    r.raise_for_status()
    return r.json().get("response", "")
