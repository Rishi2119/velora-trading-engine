@echo off
title Velora Master Launcher
color 0A

echo ========================================================
echo         VELORA TRADING PLATFORM - MASTER LAUNCHER
echo ========================================================
echo.
echo This script will start the following services in separate windows:
echo   1. FastAPI Backend Server (Port 5050)
echo   2. AI Autonomous Agent
echo   3. Next.js Web Frontend (Port 3000)
echo.
echo Press any key to start all services...
pause >nul

echo.
echo [1/3] Starting FastAPI Backend...
start "Velora Backend API" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 5050"

timeout /t 3 /nobreak >nul

echo [2/3] Starting AI Autonomous Agent...
start "Velora AI Agent" cmd /k "cd /d %~dp0\autonomous_agent && python main.py"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Next.js Web Frontend...
start "Velora Web Frontend" cmd /k "cd /d %~dp0\web_frontend && npm run dev"

echo.
echo ========================================================
echo All services have been instructed to start!
echo Please check the newly opened windows for any errors.
echo.
echo - Backend API is available at: http://localhost:5050/docs
echo - Web Frontend is available at: http://localhost:3000
echo ========================================================
echo.
pause
