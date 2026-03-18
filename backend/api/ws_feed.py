"""
WebSocket live feed for Velora backend.
Broadcasts engine events, positions, and heartbeats to all connected clients.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Set
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages all active WebSocket connections."""

    def __init__(self):
        self.active: Set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self.active.add(ws)
        logger.info(f"WS connected | clients={len(self.active)}")

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self.active.discard(ws)
        logger.info(f"WS disconnected | clients={len(self.active)}")

    async def broadcast(self, message: dict) -> None:
        """Broadcast JSON message to all connected clients."""
        if not self.active:
            return
        data = json.dumps(message, default=str)
        dead = set()
        for ws in list(self.active):
            try:
                await ws.send_text(data)
            except Exception:
                dead.add(ws)
        # Clean up dead connections
        if dead:
            async with self._lock:
                self.active -= dead

    async def send_to(self, ws: WebSocket, message: dict) -> None:
        """Send message to a single client."""
        try:
            await ws.send_text(json.dumps(message, default=str))
        except Exception:
            await self.disconnect(ws)

    @property
    def count(self) -> int:
        return len(self.active)


# Singleton
manager = ConnectionManager()


# ── Event type constants ───────────────────────────────────────────────────────
class EventType:
    HEARTBEAT = "heartbeat"
    TRADE_OPENED = "trade_opened"
    TRADE_CLOSED = "trade_closed"
    KILL_SWITCH = "kill_switch"
    ENGINE_STATUS = "engine_status"
    POSITION_UPDATE = "position_update"
    ALERT = "alert"
    ERROR = "error"


def make_event(event_type: str, data: dict = None, severity: str = "info") -> dict:
    """Create a standardized WebSocket event payload."""
    return {
        "type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "severity": severity,
        "data": data or {},
    }


async def ws_feed_handler(websocket: WebSocket):
    """
    WebSocket endpoint handler.
    Sends heartbeat every 5 seconds.
    Receives client ping/pong messages.
    """
    await manager.connect(websocket)

    # Send welcome event
    await manager.send_to(websocket, make_event(
        EventType.ENGINE_STATUS,
        {"status": "connected", "clients": manager.count},
        "info"
    ))

    try:
        while True:
            # Heartbeat every 5s (also keeps connection alive)
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                # Echo ping back as pong
                if msg == "ping":
                    await manager.send_to(websocket, {"type": "pong",
                                                      "timestamp": datetime.now(timezone.utc).isoformat()})
            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    from backend.utils.mt5_manager import mt5_manager
                    mt5_status = {"connected": mt5_manager.connected}
                except Exception:
                    mt5_status = {"connected": False}

                await manager.send_to(websocket, make_event(
                    EventType.HEARTBEAT,
                    {"clients": manager.count, "mt5": mt5_status},
                    "info"
                ))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WS handler error: {e}")
    finally:
        await manager.disconnect(websocket)
