@echo off
REM ============================================================
REM  Velora — Autonomous AI Agent Startup Script
REM  NOTE: Start the Mobile API (start_api.bat) FIRST.
REM ============================================================

title Velora AI Agent

cd /d "%~dp0\autonomous_agent"

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   VELORA AUTONOMOUS AI AGENT — v2.0      ║
echo  ╚══════════════════════════════════════════╝
echo.

REM Try project venv first
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
) else if exist "..\venv\Scripts\python.exe" (
    set PYTHON=..\venv\Scripts\python.exe
) else (
    set PYTHON=python
)

echo  [1/3] Installing / verifying agent dependencies...
%PYTHON% -m pip install requests pyyaml python-dotenv --quiet

echo  [2/3] Loading environment variables...
if exist ".env" (
    echo  Found .env file. API keys loaded.
) else (
    echo  WARNING: No .env file found in autonomous_agent/.
    echo  Create one with: KIMI_API_KEY=your_key_here
    echo  Agent will run in SIMULATION mode without a key.
)

echo  [3/3] Starting autonomous agent loop...
echo.
echo  Config: autonomous_agent/config.yaml
echo  Memory: autonomous_agent/data/memory.json
echo  Logs:   autonomous_agent/logs/
echo.
echo  Set trading.enable_live_execution: true in config.yaml
echo  to enable real MT5 trade execution.
echo.
echo  Press Ctrl+C to stop the agent.
echo.

%PYTHON% main.py

pause
