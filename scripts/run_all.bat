@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ===================================================
echo       AI MINDS SYSTEM - STARTUP SCRIPT
echo ===================================================
echo Project Root: %CD%

:: 0. Create Logs Dir
if not exist "logs" mkdir logs

:: 1. Check Dependencies (Ollama)
echo [1/5] Checking Ollama Service...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Ollama is NOT reachable at localhost:11434.
    echo Please open a new terminal and run "ollama serve".
    pause
    exit /b
)
echo [OK] Ollama is running.

:: 2. Check Virtual Environment
echo [2/5] Checking Virtual Environment...
set "VENV_PYTHON=%~dp0..\venv\Scripts\python.exe"
if not exist "!VENV_PYTHON!" (
    echo [ERROR] Virtual environment python not found at: "!VENV_PYTHON!"
    echo Please run scripts\setup_env.bat first.
    pause
    exit /b
)
echo [OK] Python found: !VENV_PYTHON!

:: 3. Verify Modules
echo [3/5] Verifying System Modules...
"!VENV_PYTHON!" -c "import uvicorn; print('uvicorn ok')" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] uvicorn not installed. Run setup_env.bat.
    pause
    exit /b
)
"!VENV_PYTHON!" -c "import streamlit; print('streamlit ok')" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] streamlit not installed. Run setup_env.bat.
    pause
    exit /b
)
"!VENV_PYTHON!" -c "import backend.app" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to import backend.app. Check logs or run_all_debug.bat.
    pause
    exit /b
)
echo [OK] Modules verified.

:: 4. Launch Backend
echo [4/5] Launching Backend Server...
:: We use 'start' to run in a separate window.
:: The window title will be "AI MINDS Backend"
:: We execute "venv python -m uvicorn ..." to be sure.
start "AI MINDS Backend" cmd /k "title AI MINDS Backend && call venv\Scripts\activate && python -m uvicorn backend.app:app --reload --port 8000 --host 127.0.0.1"

echo Waiting 5 seconds for backend to initialize...
timeout /t 5 /nobreak >nul

:: 5. Launch Frontend
echo [5/5] Launching Frontend Interface...
start "AI MINDS Frontend" cmd /k "title AI MINDS Frontend && call venv\Scripts\activate && python -m streamlit run frontend/ui.py"

echo ===================================================
echo SYSTEM RUNNING!
echo  - Backend: http://127.0.0.1:8000/docs
echo  - Frontend: http://localhost:8501
echo  - Drop files to: %CD%\inbox
echo ===================================================
echo (Close this window to stop nothing - close the other windows to stop services)
pause
