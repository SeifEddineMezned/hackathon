import subprocess
import os
import logging
from backend.config import WHISPER_EXE, WHISPER_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def transcribe_audio(audio_path: str) -> str:
    """Uses local whisper.cpp to transcribe audio file."""
    if not os.path.exists(audio_path):
        logger.error(f"File not found: {audio_path}")
        return ""
    
    # Run whisper with text output to stdout or file
    # Using subprocess to capture output
    command = [
        WHISPER_EXE,
        "-m", WHISPER_MODEL,
        "-f", audio_path,
        "-otxt", # Outputs .txt file alongside input
        "-np"   # No progress bar to keep stdout clean
    ]
    
    try:
        logger.info(f"Running Whisper: {' '.join(command)}")
        subprocess.run(command, check=True, timeout=600, capture_output=True)
        
        # Read the generated .txt file
        txt_path = audio_path + ".txt"
        if os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Clean up default txt output if desired, or keep it as artifact? 
            # User wants persistent audio files, maybe keep text too as cache.
            # But we return the content for ingestion.
            return content.strip()
        else:
            logger.error(f"Whisper output file not found: {txt_path}")
            return ""
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Whisper command failed: {e.stderr.decode('utf-8')}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error in whisper transcription: {e}")
        return ""
