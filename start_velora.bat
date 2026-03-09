@echo off
echo =================================================
echo   Starting Velora Institutional Trading Platform
echo =================================================

if not exist .env (
    echo Creating .env from .env.example...
    copy .env.example .env
)

echo Building and starting Docker containers...
docker-compose up -d --build

echo.
echo Velora Services are starting up:
echo - Frontend Dashboard:  http://localhost:3000
echo - FastAPI Backend:     http://localhost:8000/docs
echo - MT5 API Proxy:       http://localhost:5050
echo.
echo To view logs, run: docker-compose logs -f
pause
