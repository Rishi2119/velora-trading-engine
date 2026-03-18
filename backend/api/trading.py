"""
Velora API — Trading
Provides real-time MT5 data and trade execution endpoints directly via MT5 module.
"""
import logging
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from backend.config.settings import settings
from backend.utils.security import get_current_user
from backend.utils.mt5_manager import mt5_manager
from backend.utils.mt5_trade_executor import mt5_trade_executor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trading", tags=["Trading"])

KILL_SWITCH_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "KILL_SWITCH.txt")

# ── Demo fallback data ────────────────────────────────────────────────────────

def _demo_stats():
    return {
        "account_balance": 500.0, "equity": 498.25, "open_pnl": -1.75,
        "currency": "USD", "total_pnl": 142.30, "win_rate": 62.1,
        "total_trades": 87, "winning_trades": 54, "losing_trades": 33,
        "open_trades_count": 1, "avg_rr": 3.2, "max_drawdown": -145.0,
        "profit_factor": 2.1, "kill_switch_active": False,
        "mt5_connected": False, "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "demo_mode": True,
    }

# ── Schemas ───────────────────────────────────────────────────────────────────

class ExecuteTradeRequest(BaseModel):
    symbol: str
    direction: str  # BUY / SELL
    lots: float = 0.01
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    comment: Optional[str] = "Velora"

class ConnectRequest(BaseModel):
    account: str
    password: str
    server: str

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/stats")
async def get_stats():
    """Account stats — live from MT5 or demo fallback."""
    if mt5_manager.connected:
        perf = mt5_manager.get_performance_summary(days=30)
        open_positions = mt5_manager.get_open_positions()
        info = mt5_manager.get_account_info()
        kill_active = os.path.exists(KILL_SWITCH_PATH)

        if not perf: perf = {}

        balance  = info.balance if info else perf.get("balance", 500)
        equity   = info.equity if info else perf.get("equity", 500)
        profit   = info.profit if info else perf.get("profit", 0)
        currency = info.currency if info else "USD"

        return {
            "account_balance": balance,
            "equity": equity,
            "open_pnl": profit,
            "currency": currency,
            "total_pnl": perf.get("total_pnl", 0),
            "win_rate": perf.get("win_rate", 0),
            "total_trades": perf.get("total_trades", 0),
            "winning_trades": perf.get("winning_trades", 0),
            "losing_trades": perf.get("losing_trades", 0),
            "open_trades_count": len(open_positions),
            "avg_rr": perf.get("avg_rr", 0),
            "max_drawdown": perf.get("max_drawdown", 0),
            "profit_factor": perf.get("profit_factor", 0),
            "kill_switch_active": kill_active,
            "mt5_connected": True,
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    return _demo_stats()


@router.get("/open-positions")
async def get_open_positions():
    """Currently open positions."""
    if mt5_manager.connected:
        positions = mt5_manager.get_open_positions()
        return {"trades": positions, "count": len(positions), "live": True}
    return {"trades": [], "count": 0, "live": False, "demo_mode": True}


@router.get("/history")
async def get_trade_history(days: int = Query(30, ge=1, le=365)):
    """Closed trade history."""
    if mt5_manager.connected:
        closed = mt5_manager.get_trade_history(days=days)
        return {"trades": closed, "count": len(closed), "live": True}
    return {"trades": [], "count": 0, "live": False, "demo_mode": True}


@router.get("/performance")
async def get_performance(days: int = Query(30, ge=1, le=365)):
    """Daily PnL and performance summary."""
    if mt5_manager.connected:
        perf = mt5_manager.get_performance_summary(days=days) or {}
        return {
            "daily": perf.get("daily", [])[-days:],
            "summary": {
                "total_pnl": perf.get("total_pnl", 0),
                "win_rate": perf.get("win_rate", 0),
                "profit_factor": perf.get("profit_factor", 0),
                "avg_rr": perf.get("avg_rr", 0),
                "max_drawdown": perf.get("max_drawdown", 0),
                "balance": perf.get("balance", 0),
                "equity": perf.get("equity", 0),
            },
            "live": True,
        }
    return {"daily": [], "summary": {}, "live": False, "demo_mode": True}


@router.get("/kill-switch")
async def get_kill_switch():
    """Kill switch status."""
    return {"active": os.path.exists(KILL_SWITCH_PATH)}


@router.post("/kill-switch/activate")
async def activate_kill_switch(current: dict = Depends(get_current_user)):
    """Activate the kill switch (requires auth)."""
    with open(KILL_SWITCH_PATH, "w") as f:
        f.write(f"Kill switch activated via unified API at {datetime.now()}\n")
    return {"success": True, "active": True}


@router.delete("/kill-switch")
async def deactivate_kill_switch(current: dict = Depends(get_current_user)):
    """Deactivate the kill switch (requires auth)."""
    if os.path.exists(KILL_SWITCH_PATH):
        os.remove(KILL_SWITCH_PATH)
    return {"success": True, "active": False}


@router.get("/mt5/status")
async def get_mt5_status():
    """MT5 connection status."""
    if not mt5_manager.connected:
        return {
            "connected": False,
            "error": mt5_manager.last_error,
            "account": None,
        }
    info = mt5_manager.get_account_info()
    return {
        "connected": True,
        "account": {
            "broker": getattr(info, 'company', ""),
            "login": str(getattr(info, 'login', "")),
            "server": getattr(info, 'server', ""),
            "balance": round(getattr(info, 'balance', 0), 2),
            "equity": round(getattr(info, 'equity', 0), 2),
            "profit": round(getattr(info, 'profit', 0), 2),
            "currency": getattr(info, 'currency', "USD"),
            "leverage": getattr(info, 'leverage', 0),
            "account_type": "Demo" if "demo" in str(getattr(info, 'server', "")).lower() else "Live",
        } if info else None
    }


@router.post("/mt5/connect")
async def connect_mt5(body: ConnectRequest, current: dict = Depends(get_current_user)):
    """Connect to MT5."""
    try:
        account_int = int(body.account)
    except ValueError:
        raise HTTPException(status_code=400, detail="Account must be an integer.")
    result = mt5_manager.connect(account_int, body.password, body.server)
    return result


@router.post("/mt5/disconnect")
async def disconnect_mt5(current: dict = Depends(get_current_user)):
    """Disconnect from MT5."""
    mt5_manager.disconnect()
    return {"connected": False, "message": "Done"}


@router.post("/execute")
async def execute_trade(body: ExecuteTradeRequest, current: dict = Depends(get_current_user)):
    """Execute a valid trade over MT5 API."""
    if not mt5_manager.connected:
        raise HTTPException(status_code=400, detail="MT5 is not connected.")
    
    result = mt5_trade_executor.place_order(
        symbol=body.symbol,
        direction=body.direction,
        volume=body.lots,
        sl=body.stop_loss or 0.0,
        tp=body.take_profit or 0.0,
        comment=body.comment or "Velora"
    )

    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Trade execution failed"))

    return result

@router.get("/strategies")
async def get_strategies():
    """Configured trading strategies status."""
    return {
        "volatility_breakout": True,
        "london_breakout": True,
        "aggressive_trend": True,
        "mean_reversion": True,
        "demo_mode": False if mt5_manager.connected else True,
    }


@router.put("/strategies")
async def update_strategies(body: dict, current: dict = Depends(get_current_user)):
    """Enable/disable strategies."""
    return {"success": True}
