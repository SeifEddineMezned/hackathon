# AI MINDS Cognitive Assistant

A fully local, multimodal cognitive assistant system built for secure and personalized memory management.

## Features
- **Multimodal Ingestion**: Automatically processes Text, PDFs, Images, and Audio.
- **Local Inference**: Uses Ollama (Qwen2.5:3b, Phi:2.7b) and Whisper.cpp locally. No cloud APIs.
- **Persistent Memory**: SQLite + FAISS for retrieval-augmented generation (RAG).
- **Actionable Insights**: Extracts tasks, entities, and summaries automatically.
- **Verification**: Self-checking mechanism to flag hallucinations or unsupported claims.

## Prerequisites
1. **Python 3.10+** installed on Windows.
2. **Ollama** installed and running (`ollama serve`).
   - Pull required models:
     ```bash
     ollama pull qwen2.5:3b
     ollama pull nomic-embed-text
     ollama pull qwen2.5-vl:3b
     ollama pull phi:2.7b
     ```
3. **Whisper.cpp** installed (optional for audio).
   - Expected path: `C:\whisper\main.exe`
   - Model path: `C:\whisper\models\ggml-small.bin`

## fast Setup
1. Clone/Download this repo to `C:\Users\msi\Desktop\hack`.
2. Open a terminal in `C:\Users\msi\Desktop\hack`.
3. Run setup script:
   ```cmd
   scripts\setup_env.bat
   ```
   This creates a virtual environment and installs dependencies.

## Running the System
1. Keep Ollama running in background.
2. Launch the full system:
   ```cmd
   scripts\run_all.bat
   ```
3. Two windows will open:
   - **Backend**: FastAPI server logs (port 8000).
   - **Frontend**: Streamlit interface (opens in browser).

## Usage & Demo Flows

### 1. Ingestion
Drop files into the `inbox/` folders:
- **Text/Markdown**: Copy a `.txt` or `.md` file to `inbox/text/`.
- **PDF Documents**: Copy a `.pdf` to `inbox/docs/`.
- **Images**: Copy a `.jpg` or `.png` to `inbox/images/`.
- **Audio**: Copy a `.wav` or `.mp3` to `inbox/audio/`.

Watch the backend console; you will see "Processing..." logs.

### 2. Querying Memory
Go to the **Chat** tab in the UI.
- Ask: "What did I just upload?"
- Ask: "Summary of the last document."
- Ask specific questions based on your files.

Check the **Confidence Score** and **Evidence citations**.

### 3. Action Items
Go to the **Action Items** tab to see extracted tasks from your documents/meetings.

## Verification Demo
1. Upload a document about "Project Alpha deadline is Friday".
2. Ask "When is Project Alpha due?" -> High confidence.
3. Ask "Who is the CEO of Project Alpha?" (if not in text) -> Low confidence/Uncertainty flag.

## Troubleshooting
- **Ollama Connection Error**: Ensure `ollama serve` is running.
- **Whisper Error**: Check paths in `backend/config.py`.
- **Dependencies**: Re-run `scripts/setup_env.bat`.
