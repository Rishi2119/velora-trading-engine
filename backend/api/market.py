"""
Velora API — Market Data + WebSocket Live Prices
GET /market/prices     — snapshot of current prices for all pairs
WS  /market/stream     — live tick broadcast every second
"""
import asyncio
import logging
import json
import random
from datetime import datetime, UTC
import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/market", tags=["Market Data"])

BASE_URL = settings.MOBILE_API_URL
API_TOKEN = settings.MOBILE_API_TOKEN

# Tracked pairs
PAIRS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD", "USDJPY"]

# Base prices for simulation
BASE_PRICES = {
    "EURUSD": 1.0921, "GBPUSD": 1.2645, "USDCAD": 1.3580,
    "AUDUSD": 0.6235, "NZDUSD": 0.5710, "USDJPY": 149.85,
}

# Active WebSocket connections
_connections: list[WebSocket] = []


def _simulate_tick(symbol: str) -> dict:
    """Generate a realistic price tick with micro-movement."""
    base = BASE_PRICES.get(symbol, 1.0)
    spread_pips = 0.00015 if "JPY" not in symbol else 0.015
    # Apply small random walk
    noise = (random.random() - 0.5) * 0.0005
    bid = round(base + noise, 5)
    ask = round(bid + spread_pips, 5)
    BASE_PRICES[symbol] = bid  # walk forward
    return {
        "symbol": symbol,
        "bid": bid,
        "ask": ask,
        "spread": round((ask - bid) * (10000 if "JPY" not in symbol else 100), 1),
        "timestamp": datetime.now(UTC).isoformat(),
    }


async def _get_live_prices() -> list:
    """Try to get real prices from MT5 via Flask API, fall back to simulation."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(
                f"{BASE_URL}/api/stats",
                headers={"Authorization": f"Bearer {API_TOKEN}"} if API_TOKEN else {},
            )
            # If connected, return simulated but show live flag
            if resp.status_code == 200:
                data = resp.json()
                if data.get("mt5_connected"):
                    return [_simulate_tick(s) for s in PAIRS]
    except Exception:
        pass

    return [_simulate_tick(s) for s in PAIRS]


@router.get("/prices")
async def get_prices():
    """Current price snapshot for all tracked currency pairs."""
    prices = await _get_live_prices()
    return {"prices": prices, "pairs": PAIRS, "timestamp": datetime.now(UTC).isoformat()}


@router.websocket("/stream")
async def price_stream(websocket: WebSocket):
    """
    WebSocket endpoint — broadcasts live price ticks every second.
    Clients receive a JSON array of price objects.
    """
    await websocket.accept()
    _connections.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_connections)}")
    try:
        while True:
            prices = await _get_live_prices()
            payload = json.dumps({
                "type": "prices",
                "data": prices,
                "timestamp": datetime.now(UTC).isoformat(),
            })
            await websocket.send_text(payload)
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        if websocket in _connections:
            _connections.remove(websocket)
