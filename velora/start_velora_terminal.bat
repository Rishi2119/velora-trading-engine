@echo off
REM ================================================================
REM  VELORA TRADE TERMINAL - Web App Launcher
REM  Starts the Next.js web_app on port 3000 (or 3001 if 3000 is busy)
REM ================================================================

setlocal
cd /d %~dp0

REM Ensure we are in the velora root
echo [1/3] Changing directory to velora/web_app...
cd web_app || (
  echo [ERROR] Could not change to velora/web_app. Check folder structure.
  pause
  exit /b 1
)

REM Optional: install deps if node_modules is missing
if not exist node_modules (
  echo [2/3] Installing npm dependencies (first-time setup)...
  npm install
  if errorlevel 1 (
    echo [ERROR] npm install failed.
    pause
    exit /b 1
  )
)

echo [3/3] Starting Velora web app (Next.js dev server)...
npm run dev

endlocal
