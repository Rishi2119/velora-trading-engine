@echo off
REM ============================================================
REM Quick Start - Just Web Frontend
REM ============================================================

echo Starting Web Frontend...
cd /d "%~dp0web_frontend"

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

echo.
echo Starting Next.js on http://localhost:3000
echo Press Ctrl+C to stop
echo.
call npm run dev
