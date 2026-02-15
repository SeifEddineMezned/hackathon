@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ===================================================
echo   AI MINDS SYSTEM - DEBUG MODE (SINGLE WINDOW)
echo ===================================================
echo Project Root: %CD%

:: 1. Check Python
set "VENV_PYTHON=%~dp0..\venv\Scripts\python.exe"
if not exist "!VENV_PYTHON!" (
    echo [ERROR] Virtual environment python not found at: "!VENV_PYTHON!"
    echo Please run scripts\setup_env.bat first.
    pause
    exit /b
)
echo [OK] Python found: !VENV_PYTHON!

:: 2. Check Ollama
echo [1/2] Checking Ollama Service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is NOT reachable at localhost:11434.
    echo Please ensure "ollama serve" is running!
) else (
    echo [OK] Ollama is running.
)

:: 3. Launch Backend in Foreground
echo [3/3] Launching Backend Server in FOREGROUND...
echo (You will see all python output here. If it crashes, copy the traceback.)
echo.
echo Press Ctrl+C to stop.
echo.

"!VENV_PYTHON!" -m uvicorn backend.app:app --reload --port 8000 --host 127.0.0.1 --log-level debug

echo.
echo Backend stopped.
pause
