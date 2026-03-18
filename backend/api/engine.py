"""
Backend API — Engine Control
GET  /api/v1/engine/status     — current engine state, kill switch, MT5 status
POST /api/v1/engine/kill       — activate kill switch (auth required)
POST /api/v1/engine/unkill     — deactivate kill switch (auth required)
POST /api/v1/engine/restart    — signal engine restart (creates restart flag)
GET  /api/v1/engine/heartbeat  — last heartbeat from engine process
"""
import os
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from backend.utils.security import get_current_user
from backend.utils.mt5_manager import mt5_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/engine", tags=["Engine"])

_RESTART_FLAG = "RESTART_ENGINE.flag"


# ── Status ────────────────────────────────────────────────────────────────────

@router.get("/status")
async def get_engine_status():
    """Full engine status snapshot."""
    # Kill switch state
    try:
        from kill_switch import is_active as ks_active, get_status as ks_status
        ks = ks_status()
    except Exception:
        ks = {"active": os.path.exists("KILL_SWITCH.txt"), "reason": "", "activated_at": None}

    # Risk state
    try:
        from risk import get_risk_manager
        rm = get_risk_manager()
        risk_stats = rm.get_stats()
    except Exception as e:
        risk_stats = {"error": str(e)}

    # Circuit breaker
    try:
        from circuit_breaker import drawdown_circuit_breaker
        cb_status = drawdown_circuit_breaker.get_status()
    except Exception:
        cb_status = {}

    # Session
    try:
        from session_filter import get_session_info
        session = get_session_info()
    except Exception:
        session = {"session": "unknown", "active": False}

    # MT5
    mt5_connected = mt5_manager.connected if mt5_manager else False
    acc_info = None
    if mt5_connected:
        raw = mt5_manager.get_account_info()
        if raw:
            acc_info = {
                "balance": round(getattr(raw, "balance", 0), 2),
                "equity": round(getattr(raw, "equity", 0), 2),
                "free_margin": round(getattr(raw, "margin_free", 0), 2),
                "profit": round(getattr(raw, "profit", 0), 2),
                "currency": getattr(raw, "currency", "USD"),
            }

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "kill_switch": ks,
        "mt5": {"connected": mt5_connected, "account": acc_info},
        "risk": risk_stats,
        "circuit_breaker": cb_status,
        "session": session,
        "restart_pending": os.path.exists(_RESTART_FLAG),
    }


@router.get("/heartbeat")
async def get_heartbeat():
    """Lightweight ping — used by UptimeRobot and watchdogs."""
    return {
        "status": "alive",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mt5_connected": mt5_manager.connected if mt5_manager else False,
    }


# ── Kill switch ───────────────────────────────────────────────────────────────

class KillReason(BaseModel):
    reason: str = "API kill"


@router.post("/kill")
async def kill_engine(body: KillReason, current: dict = Depends(get_current_user)):
    """Activate kill switch. Closes all positions and halts trading."""
    try:
        from kill_switch import activate
        activate(body.reason)
        # Also broadcast via WebSocket
        _broadcast_ws("kill_switch", {"active": True, "reason": body.reason})
        return {"success": True, "active": True, "reason": body.reason}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unkill")
async def unkill_engine(body: KillReason, current: dict = Depends(get_current_user)):
    """Deactivate kill switch. Engine will resume on next loop."""
    try:
        from kill_switch import deactivate
        deactivate(body.reason)
        _broadcast_ws("kill_switch", {"active": False, "reason": body.reason})
        return {"success": True, "active": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart")
async def restart_engine(current: dict = Depends(get_current_user)):
    """Create restart flag for watchdog to pick up."""
    with open(_RESTART_FLAG, "w") as f:
        f.write(f"restart requested at {datetime.now(timezone.utc).isoformat()}")
    return {"success": True, "message": "Restart flag set. Watchdog will restart engine."}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _broadcast_ws(event_type: str, data: dict):
    """Fire-and-forget: broadcast to all WS clients (non-async context)."""
    try:
        import asyncio
        from backend.api.ws_feed import manager, make_event
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(manager.broadcast(make_event(event_type, data)))
    except Exception as e:
        logger.debug(f"WS broadcast failed: {e}")
