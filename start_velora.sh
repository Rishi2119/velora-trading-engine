#!/bin/bash
# Velora Startup Script

echo "================================================="
echo "  Starting Velora Institutional Trading Platform"
echo "================================================="

# Check if .env exists, if not copy from example
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

echo "Building and starting Docker containers..."
docker-compose up -d --build

echo ""
echo "Velora Services are starting up:"
echo "- Frontend Dashboard:  http://localhost:3000"
echo "- FastAPI Backend:     http://localhost:8000/docs"
echo "- MT5 API Proxy:       http://localhost:5050"
echo ""
echo "To view logs, run: docker-compose logs -f"
