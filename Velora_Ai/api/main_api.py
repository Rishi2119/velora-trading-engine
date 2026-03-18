# // turbo
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from loguru import logger
from core.mt5_connector import connector
from core.risk_manager import risk_manager
from ai.deepseek_brain import brain
from ai.strategy_loader import strategy_loader
from config.settings import config
from core.strategy import strategy_layer

app = FastAPI(title="Velora AI Engine API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/health")
def health():
    return {"status": "online", "version": "2.0", "engine": "Velora AI"}

@app.get("/api/account")
def get_account():
    return connector.get_account()

@app.get("/api/positions")
def get_positions():
    return connector.get_open_positions()

@app.get("/api/strategies")
def get_strategies():
    return strategy_loader.strategies

@app.get("/api/regime")
async def get_regime():
    account = connector.get_account()
    return await brain.analyze_market_regime({"account": account})

@app.get("/api/risk/status")
def get_risk_status():
    account = connector.get_account()
    positions = connector.get_open_positions()
    check = risk_manager.check_trade_allowed(account, positions)
    return {
        "trade_allowed": check["allowed"],
        "reason": check["reason"],
        "daily_pnl": risk_manager.get_daily_pnl(),
        "open_trades": len(positions),
        "max_concurrent": config.MAX_CONCURRENT_TRADES,
    }

@app.post("/api/engine/start")
async def start_engine(background: BackgroundTasks):
    from core.trading_engine import engine
    background.add_task(engine.run, 300)
    return {"status": "started", "message": "Velora engine running in background"}

@app.post("/api/engine/stop")
def stop_engine(payload: Optional[Dict[str, Any]] = None):
    from core.trading_engine import engine
    try:
        engine.stop()
        return {"status": "stopped", "message": "Engine shutdown initiated safely"}
    except Exception as e:
        logger.error(f"Stop error: {e}")
        return {"status": "error", "message": str(e)}

@app.delete("/api/trade/{ticket}")
def close_trade(ticket: int):
    result = connector.close_trade(ticket)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result

@app.get("/api/performance/review")
async def daily_review():
    return await brain.review_performance([], connector.get_account())

@app.post("/api/analyze")
async def analyze_market(data: Dict[str, Any]):
    """
    Triggers the Institutional strategy + AI Decision layer.
    """
    decision = await strategy_layer.execute(data)
    return decision

@app.websocket("/ws/feed")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Stream account and position data every 2 seconds
            data = {
                "account": connector.get_account(),
                "positions": connector.get_open_positions(),
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send_json(data)
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close()

from datetime import datetime
