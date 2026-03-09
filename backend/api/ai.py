"""
Velora API — AI Agent Control
Proxies to the autonomous_agent via agent_manager in mobile_api.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from backend.config.settings import settings
from backend.utils.security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["AI Agent"])

BASE_URL = settings.MOBILE_API_URL
API_TOKEN = settings.MOBILE_API_TOKEN


def _headers():
    return {"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {}


def _demo_agent_status():
    return {
        "is_running": False,
        "latest_thought": "Agent is in simulation mode. No API key configured.",
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
            resp = await client.get(f"{BASE_URL}/api/agent/status", headers=_headers())
            return resp.json()
    except Exception as e:
        logger.debug(f"Agent status proxy failed: {e}")
        return _demo_agent_status()


@router.get("/thoughts")
async def get_agent_thoughts():
    """Live agent thought and decision feed."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{BASE_URL}/api/agent/thoughts", headers=_headers())
            return resp.json()
    except Exception as e:
        logger.debug(f"Agent thoughts proxy failed: {e}")
        return _demo_agent_status()


@router.post("/start")
async def start_agent(current: dict = Depends(get_current_user)):
    """Start the autonomous AI agent."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{BASE_URL}/api/agent/start", headers=_headers())
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not reach trading API: {e}")


@router.post("/stop")
async def stop_agent(current: dict = Depends(get_current_user)):
    """Stop the autonomous AI agent."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(f"{BASE_URL}/api/agent/stop", headers=_headers())
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Could not reach trading API: {e}")


@router.post("/enable-trading")
async def enable_agent_trading(body: dict, current: dict = Depends(get_current_user)):
    """Toggle live trading mode for the AI agent."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"{BASE_URL}/api/agent/enable-trading",
                headers=_headers(),
                json=body,
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))
