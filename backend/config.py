import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
INBOX_DIR = BASE_DIR / "inbox"
DB_PATH = BASE_DIR / "backend" / "ai_minds.db"
VECTOR_STORE_PATH = BASE_DIR / "backend" / "vector_store"

# Folder Monitoring
WATCH_DIRS = {
    "text": INBOX_DIR / "text",
    "docs": INBOX_DIR / "docs",
    "images": INBOX_DIR / "images",
    "audio": INBOX_DIR / "audio",
}

# Model Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_MAIN = "qwen2.5:3b"
MODEL_EMBEDDING = "nomic-embed-text"
MODEL_VISION = "qwen2.5-vl:3b"  # Adjusted to standard Ollama naming convention if needed
MODEL_BACKUP = "phi:2.7b"

# Whisper Configuration (Local)
WHISPER_EXE = r"C:\whisper\main.exe"
WHISPER_MODEL = r"C:\whisper\models\ggml-small.bin"

# System Settings
CONFIDENCE_THRESHOLD = 60
MAX_SEARCH_RESULTS = 5
