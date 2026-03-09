@echo off
REM ============================================================
REM Quick Start - Just Backend API (FastAPI)
REM ============================================================

echo Starting FastAPI Backend...
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r backend\requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Starting FastAPI on http://localhost:8000
echo API Docs at http://localhost:8000/docs
echo Press Ctrl+C to stop
echo.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
