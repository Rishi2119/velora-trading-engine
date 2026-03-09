@echo off
REM ============================================================
REM  Velora Trading System — Unified API Startup Script
REM  Starts the FastAPI REST API on http://0.0.0.0:5050
REM ============================================================

title Velora Mobile API

REM Ensure we are in the script's directory
cd /d "%~dp0"

echo.
echo  ╔══════════════════════════════════════╗
echo  ║   VELORA TRADING ENGINE — API v2.0   ║
echo  ╚══════════════════════════════════════╝
echo.
echo  [1/3] Checking Python environment...

REM Use absolute paths to prevent "The system cannot find the path specified" after cd
set PYTHON=python
if exist "%~dp0venv\Scripts\python.exe" (
    set PYTHON="%~dp0venv\Scripts\python.exe"
) else if exist "%~dp0..\venv\Scripts\python.exe" (
    set PYTHON="%~dp0..\venv\Scripts\python.exe"
)

echo  Using Python executable: %PYTHON%
echo  Current working directory: %CD%
echo.
echo  [2/3] Installing / verifying dependencies...
%PYTHON% -m pip install flask flask-cors MetaTrader5 pyyaml --quiet --upgrade

echo.
echo  [3/3] Launching API on http://0.0.0.0:5050 ...
echo  Server startup status: INIT
echo.
echo  Open these URLs in your browser to verify access and get your API token:
echo  1. http://127.0.0.1:5050
echo  2. http://localhost:5050
echo  (Or use your machine's LAN IP address from other devices)
echo.
echo  Press Ctrl+C to stop the server.
echo.

cd backend
echo  Changed directory to: %CD%
echo  Starting FastAPI Server...
%PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 5050

pause
