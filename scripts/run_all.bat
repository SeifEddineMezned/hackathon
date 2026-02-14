@echo off
cd /d "%~dp0\.."

echo Starting AI MINDS System...
echo Project Root: %CD%

:: Check Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama API not detected (localhost:11434).
    echo Please ensure "ollama serve" is running.
) else (
    echo Ollama detected.
)

:: Check Venv
if not exist venv (
    echo Virtual environment "venv" not found. Please run scripts\setup_env.bat first.
    pause
    exit /b
)

:: Start Backend
echo Launching Backend...
start "AI MINDS Backend" cmd /k "call venv\Scripts\activate && uvicorn backend.app:app --reload --port 8000"

:: Wait for backend init
timeout /t 5 /nobreak

:: Start Frontend
echo Launching Frontend...
start "AI MINDS Frontend" cmd /k "call venv\Scripts\activate && streamlit run frontend/ui.py"

echo System running!
echo Drop files into %CD%\inbox to see ingestion in action.
pause
