@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0\.."

echo ===================================================
echo   AI MINDS SYSTEM - FRONTEND DEBUG MODE
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

:: 2. Launch Frontend in Foreground
echo [2/2] Launching Frontend Interface in FOREGROUND...
echo (You will see all python output here. If it crashes, copy the traceback.)
echo.
echo Press Ctrl+C to stop.
echo.

"!VENV_PYTHON!" -m streamlit run frontend/ui.py --server.port 8501 --server.headless false

echo.
echo Frontend stopped.
pause
