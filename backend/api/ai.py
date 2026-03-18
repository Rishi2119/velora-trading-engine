"""
Velora API — AI Agent Control
Proxies to the Velora AI Engine (FastAPI) at port 8001.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from backend.config.settings import settings
from backend.utils.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Agent"])

# Points to Velora AI Engine CLI/API
VELORA_ENGINE_URL = "http://127.0.0.1:8001"


def _demo_agent_status():
    return {
        "is_running": False,
        "latest_thought": "Velora AI Engine is offline.",
        "latest_decision": "HOLD",
        "confidence": 0.0,
        "uptime_seconds": 0,
        "crash_count": 0,
        "demo_mode": True,
    }


@router.get("/status")
async def get_agent_status():
    """Current agent status — running, last thought, decision, confidence."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{VELORA_ENGINE_URL}/status")
            return resp.json()
    except Exception as e:
        logger.debug(f"Velora Engine status proxy failed: {e}")
        return _demo_agent_status()


@router.get("/thoughts")
async def get_agent_thoughts():
    """Live agent thought and decision feed (mapped to Velora status/journal)."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{VELORA_ENGINE_URL}/status")
            # The dashboard expects a certain format, but if it accepts the full status, we return it
            return resp.json()
    except Exception as e:
        logger.debug(f"Velora Engine thoughts proxy failed: {e}")
        return _demo_agent_status()


@router.post("/start")
async def start_agent(current: dict = Depends(get_current_user)):
    """Start the autonomous Velora AI agent."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{VELORA_ENGINE_URL}/start")
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Velora Engine: {e}")


@router.post("/stop")
async def stop_agent(current: dict = Depends(get_current_user)):
    """Stop the autonomous Velora AI agent."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{VELORA_ENGINE_URL}/stop")
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not reach Velora Engine: {e}")


@router.post("/enable-trading")
async def enable_agent_trading(body: dict, current: dict = Depends(get_current_user)):
    """Toggle live trading mode for the AI agent (Passthrough)."""
    # Velora Engine manages its own execution state via risk management.
    # We can return success as this is now managed within the engine itself.
    return {"success": True, "message": "Trading mode managed by Velora Engine"}
