@echo off
REM ================================================================
REM  VELORA TRADING ENGINE - Master Launcher
REM  Starts: Backend API + AI Agent + Web Frontend
REM  Usage: start_all.bat [paper|live]
REM ================================================================
setlocal
title Velora Master Launcher
color 0A

SET MODE=%1
IF "%MODE%"=="" SET MODE=paper
SET ROOT=%~dp0

:: ============================================================================
:: VELORA AI ENGINE — Master Launcher (UTF-8 Sanitized)
:: ============================================================================

set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"
set "PYTHONPATH=%~dp0"

echo.
echo  =============================================
echo   VELORA AI ENGINE V2.0  (2026 EDITION)
echo   [ PROTOCOL : TURBOPACK NEURAL LINK ]
echo  =============================================
echo.

:: 1. Cleanup old processes
echo [1/5] Cleaning up old processes...
taskkill /F /IM python.exe /T 2>nul
echo.

:: 2. Check environment
if not exist ".env" (
    echo [ERROR] .env file not found!
    pause
    exit /b 1
)

:: 3. Start Velora AI Engine (Core API)
echo [2/5] Starting Velora AI Engine API (Port 8001)...
start "Velora AI Engine" /min cmd /c "cd /d %~dp0Velora_Ai && ..\.venv\Scripts\python -m uvicorn api:app --host 127.0.0.1 --port 8001"
timeout /t 3 >nul

:: 4. Start Unified Backend API
echo [3/5] Starting Unified Backend API (Port 8000)...
set "BACKEND_PYTHON=python"
if exist "%~dp0backend\venv\Scripts\python.exe" set "BACKEND_PYTHON=%~dp0backend\venv\Scripts\python.exe"
start "Velora Backend" /min cmd /c "set PYTHONPATH=%~dp0 && cd /d %~dp0 && "%BACKEND_PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 >nul

:: 5. Start Web Frontend
echo [4/5] Starting Web Dashboard (Port 3000)...
start "Velora Dashboard" /min cmd /c "cd /d %~dp0web_frontend && npm run dev"
timeout /t 5 >nul

echo.
echo [5/5] ALL SERVICES LAUNCHED!
echo.
echo  - Engine API:  http://localhost:8001
echo  - Backend API: http://localhost:8000
echo  - Dashboard:   http://localhost:3000
echo.
echo Press any key to stop all services (kills python)...
pause >nul

taskkill /F /IM python.exe /T
echo DONE.
pause
