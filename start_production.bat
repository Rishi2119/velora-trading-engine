@echo off
REM ============================================================
REM Velora Trading Platform - Production Startup Script
REM ============================================================
REM This script starts all services in order:
REM 1. FastAPI Backend (port 8000)
REM 2. Flask Mobile API (port 5050)
REM 3. Web Frontend (port 3000)
REM ============================================================

echo ============================================================
echo         VELORA TRADING PLATFORM - PRODUCTION START
echo ============================================================

REM Check if Python venv exists
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found!
    echo Creating new virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r backend\requirements.txt
    pip install flask flask-cors
) else (
    call venv\Scripts\activate.bat
)

echo.
echo [1/3] Starting FastAPI Backend on port 8000...
start "Velora-Backend" cmd /c "cd /d %~dp0 && call venv\Scripts\activate.bat && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Flask Mobile API on port 5050...
start "Velora-MobileAPI" cmd /c "cd /d %~dp0 && call venv\Scripts\activate.bat && python mobile_api\app.py"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Web Frontend on port 3000...
start "Velora-Frontend" cmd /c "cd /d %~dp0\web_frontend && npm run dev"

echo.
echo ============================================================
echo                    ALL SERVICES STARTED!
echo ============================================================
echo.
echo Endpoints:
echo   - FastAPI Backend:  http://localhost:8000
echo   - FastAPI Docs:     http://localhost:8000/docs
echo   - Mobile API:       http://localhost:5050
echo   - Web Dashboard:    http://localhost:3000
echo.
echo Press any key to exit this window (services will keep running)
pause >nul
