@echo off
REM ===========================================================================
REM Organizer Chat Bot — Windows CMD runner
REM Usage:  run.bat
REM What it does:
REM   - Creates .venv on first run
REM   - Installs requirements into .venv
REM   - Runs the bot
REM Press Ctrl+C to stop.
REM ===========================================================================

setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [setup] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [error] Failed to create virtual environment.
        echo Make sure Python 3.11+ is installed and on PATH.
        exit /b 1
    )
)

echo [setup] Installing/upgrading dependencies...
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [error] Failed to install dependencies.
    exit /b 1
)

if not exist ".env" (
    echo.
    echo [setup] No .env found. Copying from .env.example...
    copy ".env.example" ".env" >nul
    echo.
    echo IMPORTANT: Edit .env and fill in your real credentials before
    echo running the bot again. See README.md for guidance.
    echo.
    exit /b 1
)

echo [run] Starting Organizer Chat Bot...
".venv\Scripts\python.exe" -m src.main
endlocal