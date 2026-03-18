"""
API Endpoints for running historical backtests.
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

# In a real app we'd fetch historical JSON/CSV or from a DB natively.
# For simplicity in this endpoint we generate dummy or fetch minimal MT5 data if available.
from backend.app.analytics.backtester import backtester
from backend.app.execution.mt5_connection import mt5_conn
from backend.app.core.config import config
import time
import uuid
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

# Simple in-memory storage for backtest results 
# (In production, write to Supabase)
jobs: Dict[str, Dict[str, Any]] = {}


class BacktestRequest(BaseModel):
    symbol: str
    timeframe_str: str = "H1"  # Not mapped fully yet
    count: int = 1000
    risk_per_trade: float = 0.01


@router.post("/run")
async def run_backtest(req: BacktestRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "RUNNING",
        "symbol": req.symbol,
        "result": None
    }
    
    # In a real scalable environment, send to Celery/SQS. We use Starlette BackgroundTasks here.
    background_tasks.add_task(_run_backtest_task, job_id, req)
    
    return {"job_id": job_id, "status": "RUNNING"}


@router.get("/{job_id}")
async def get_backtest_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


def _run_backtest_task(job_id: str, req: BacktestRequest):
    logger.info(f"Background task starting backtest {job_id} for {req.symbol}")
    
    # Try fetching real historical data if live
    df = None
    if config.engine_mode == "live" and mt5_conn.is_connected:
        try:
            # Note: Hardcoded 16384 (H1 flag in MT5 for standard setup) timeframe
            # but usually it's mt5.TIMEFRAME_H1. For safety we just use config.timeframe
            df = mt5_conn.get_rates(req.symbol, config.timeframe, req.count)
        except Exception as e:
            logger.error(f"MT5 fetch failed: {e}")
            
    if df is None or df.empty:
        # Generate dummy data for testing purposes if MT5 failed / paper mode
        logger.warning("Using synthetic OHLCV data for backtester.")
        dates = pd.date_range("2024-01-01", periods=req.count, freq="1h")
        close = np.linspace(1.1000, 1.1500, req.count) + np.random.normal(0, 0.001, req.count)
        df = pd.DataFrame({
            "time": dates,
            "open": close + 0.0005,
            "high": close + 0.0020,
            "low": close - 0.0020,
            "close": close,
            "tick_volume": 1000
        })
        
    try:
        # Override initial balance or risk if needed via the backtester singleton
        result = backtester.run_backtest(req.symbol, df)
        jobs[job_id]["status"] = "COMPLETED"
        jobs[job_id]["result"] = result
    except Exception as e:
        logger.error(f"Backtest {job_id} failed: {e}", exc_info=True)
        jobs[job_id]["status"] = "FAILED"
        jobs[job_id]["error"] = str(e)
