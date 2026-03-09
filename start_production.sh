#!/bin/bash
# ============================================================
# Velora Trading Platform - Production Startup Script (Linux/Mac)
# ============================================================

echo "============================================================"
echo "        VELORA TRADING PLATFORM - PRODUCTION START"
echo "============================================================"

# Navigate to script directory
cd "$(dirname "$0")"

# Check if Python venv exists
if [ ! -f "venv/bin/python" ]; then
    echo "[WARNING] Python virtual environment not found!"
    echo "Creating new virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r backend/requirements.txt
    pip install flask flask-cors
else
    source venv/bin/activate
fi

echo ""
echo "[1/3] Starting FastAPI Backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

sleep 3

echo "[2/3] Starting Flask Mobile API on port 5050..."
python mobile_api/app.py &
MOBILE_API_PID=$!

sleep 2

echo "[3/3] Starting Web Frontend on port 3000..."
cd web_frontend && npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================================"
echo "                   ALL SERVICES STARTED!"
echo "============================================================"
echo ""
echo "Endpoints:"
echo "  - FastAPI Backend:  http://localhost:8000"
echo "  - FastAPI Docs:     http://localhost:8000/docs"
echo "  - Mobile API:       http://localhost:5050"
echo "  - Web Dashboard:    http://localhost:3000"
echo ""
echo "PIDs:"
echo "  - Backend: $BACKEND_PID"
echo "  - Mobile API: $MOBILE_API_PID"
echo "  - Frontend: $FRONTEND_PID"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for any process to exit
wait
