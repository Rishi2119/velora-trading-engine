@echo off
TITLE Velora Engine Watchdog
echo ==============================================
echo       VELORA TRADING ENGINE WATCHDOG
echo ==============================================
echo.

:loop
echo [%time%] Starting Velora Engine...

REM Ensure virtual environment is activated if it exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Run the main backend entrypoint
python -m backend.main

set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% neq 0 (
    echo.
    echo [CRITICAL] Engine crashed with exit code %EXIT_CODE%.
    echo [%time%] Restarting in 10 seconds...
    timeout /t 10 /nobreak
    goto loop
) else (
    echo.
    echo [%time%] Engine exited cleanly (Exit code 0). Watchdog terminating.
    pause
)
