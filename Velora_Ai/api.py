"""
Velora AI — FastAPI Layer
=========================
REST API to control the Velora Engine remotely.
Enables integration with the Velora Trading Terminal.

Run:
    uvicorn api:app --host 0.0.0.0 --port 8001

Endpoints:
    GET  /status           — Engine health + account info
    POST /start            — Start background engine loop
    POST /stop             — Stop background engine loop
    POST /signal           — Run one manual inference cycle
    GET  /journal          — Recent trade journal
"""

import sys
import os
import asyncio
import time
from datetime import datetime
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import CONFIDENCE_THRESHOLD, JOURNAL_PATH
from velora_engine import VeloraEngine
from backtest_engine import BacktestEngine
from train_model import AIDecisionModel, train
from utils.logger import get_logger

log = get_logger("VeloraAPI")

app = FastAPI(
    title="Velora AI Trading Engine",
    version="1.0.0",
    description="Institutional-grade AI trading agent API",
)

from api.strategy_score import router as strategy_router
app.include_router(strategy_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

# Global state
_engine: Optional[VeloraEngine] = None
_bg_task: Optional[asyncio.Task] = None
_start_time: Optional[datetime] = None
_failure_count: int = 0
MAX_FAILURES: int = 5

def get_engine() -> VeloraEngine:
    global _engine
    if _engine is None:
        _engine = VeloraEngine()
    return _engine

async def engine_loop():
    """Background loop for the engine with circuit breaker."""
    global _failure_count
    engine = get_engine()
    log.info("Starting background engine loop...")
    try:
        while engine.running:
            try:
                # Run one cycle
                engine.run_once()
                _failure_count = 0  # Reset on success
            except Exception as e:
                _failure_count += 1
                log.error(f"Engine cycle error ({_failure_count}/{MAX_FAILURES}): {e}")
                if _failure_count >= MAX_FAILURES:
                    log.critical("Circuit breaker triggered! Stopping engine due to consecutive failures.")
                    engine.running = False
                    break
            
            # Wait 30 seconds
            await asyncio.sleep(30)
    except asyncio.CancelledError:
        log.info("Background loop cancelled.")
    finally:
        log.info("Background loop stopped.")

# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/status")
def status():
    engine = get_engine()
    acct   = None
    try:
        acct = engine.executor.get_account_info()
    except:
        pass

    uptime_sec = 0
    if _start_time and engine.running:
        uptime_sec = int((datetime.now() - _start_time).total_seconds())

    # Get latest journal entry for "latest_thought"
    latest_thought = "Velora AI Engine initialized and ready."
    latest_decision = "HOLD"
    confidence = 0.0

    if os.path.exists(JOURNAL_PATH):
        try:
            df = pd.read_csv(JOURNAL_PATH)
            if not df.empty:
                last_row = df.iloc[-1]
                latest_decision = last_row["action"]
                confidence = float(last_row["confidence"])
                latest_thought = f"Executed {latest_decision} for {last_row['symbol']} with {confidence*100:.1f}% confidence."
        except:
            pass

    return {
        "is_running":   engine.running,
        "model_ready":  engine.ai_model.is_ready,
        "latest_thought": latest_thought,
        "latest_decision": latest_decision,
        "confidence":   confidence,
        "uptime_seconds": uptime_sec,
        "open_trades":  engine.risk.open_trades if hasattr(engine.risk, "open_trades") else 0,
        "daily_pnl":    getattr(engine.risk, "daily_pnl", 0.0),
        "account":      acct,
    }

@app.post("/start")
async def start_engine():
    global _bg_task, _start_time
    engine = get_engine()
    if engine.running:
        return {"status": "already_running"}
    
    engine.running = True
    _start_time = datetime.now()
    _bg_task = asyncio.create_task(engine_loop())
    log.info("Engine start requested via API")
    return {"status": "started"}

@app.post("/stop")
async def stop_engine():
    global _bg_task
    engine = get_engine()
    if not engine.running:
        return {"status": "not_running"}
    
    engine.running = False
    if _bg_task:
        _bg_task.cancel()
        _bg_task = None
    
    log.info("Engine stop requested via API")
    return {"status": "stopped"}

@app.post("/signal")
def get_signal():
    """Run one manual inference cycle."""
    engine = get_engine()
    result = engine.run_once()
    return result

@app.get("/journal")
def get_journal(limit: int = 50):
    if not os.path.exists(JOURNAL_PATH):
        return {"trades": []}
    try:
        df = pd.read_csv(JOURNAL_PATH)
        return {"trades": df.tail(limit).to_dict(orient="records")}
    except:
        return {"trades": []}

@app.get("/health")
def health():
    return {"status": "ok", "engine": "Velora AI v1.0", "running": get_engine().running}
