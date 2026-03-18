@echo off
REM ================================================================
REM  VELORA UNIFIED STARTUP — Institutional AI Trading Suite
REM  Starts: Backend API + Trading Engine + Web Dashboard + Mobile
REM ================================================================
setlocal

SET MODE=%1
IF "%MODE%"=="" SET MODE=paper

SET ROOT=%~dp0
SET BACKEND_DIR=%ROOT%backend
SET FRONTEND_DIR=%ROOT%web_frontend
SET MOBILE_DIR=%ROOT%velora_flutter

echo.
echo ================================================================
echo  VELORA TRADING SYSTEM — UNIFIED LAUNCHER
echo  Mode: %MODE%
echo ================================================================
echo.

REM 1. Pre-flight Check
IF NOT EXIST "%ROOT%.env" (
    echo [!] Missing .env file. Copying .env.example...
    copy "%ROOT%.env.example" "%ROOT%.env"
)

REM 2. Start Trading Engine (Background logic)
echo [1/4] Launching High-Frequency Engine...
start "Velora Engine" cmd /k "cd /d %ROOT%Velora_Ai && ..\.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8001"
timeout /t 2 /nobreak >nul

REM 3. Start Backend API (REST + WebSocket)
echo [2/4] Launching Systems API...
start "Velora Backend" cmd /k "set PYTHONPATH=%ROOT% && cd /d %ROOT% && backend\venv\Scripts\python.exe -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 2 /nobreak >nul

REM 4. Start Web Dashboard (Next.js)
echo [3/4] Launching Web Dashboard (http://localhost:3000)...
start "Velora Web" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
timeout /t 2 /nobreak >nul

REM 5. Start Flutter Mobile App
echo [4/4] Launching Flutter Mobile App...
start "Velora Mobile" cmd /k "cd /d %MOBILE_DIR% && flutter run"

echo.
echo ================================================================
echo  SYSTEMS OPERATIONAL
echo  Web View:    http://localhost:3000/dashboard
echo  API Docs:    http://localhost:8000/docs
echo  Environment: %MODE%
echo ================================================================
echo.
echo Press ANY KEY to SHUTDOWN ALL components safely...
pause >nul

echo Shutting down...
taskkill /FI "WINDOWTITLE eq Velora Engine" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Velora Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Velora Web" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Velora Mobile" /F >nul 2>&1

echo [SUCCESS] Velora shutdown sequence complete.
pause
