@echo off
cd /d "%~dp0\.."
echo Project Root: %CD%

echo Setting up AI MINDS Environment...

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3 not found in PATH!
    pause
    exit /b
)

:: Create Venv if not exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists.
)

:: Activate & Install
echo Installing dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup Complete!
echo You can run the system using: scripts\run_all.bat
pause
