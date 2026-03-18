"""
WebSocket Feed Manager.
Manages real-time WebSockets to push engine state, trades, and health 
updates to the frontend applications.
"""
import json
import logging
from typing import Set, Dict, Any, Optional
from datetime import datetime, UTC
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections for event broadcasting."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast(self, message_type: str, data: Dict[str, Any], severity: str = "info"):
        """
        Broadcast JSON data to all connected clients.
        Schema: { type, timestamp, severity, data }
        """
        if not self.active_connections:
            return
            
        payload = {
            "type": message_type,
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": severity,
            "data": data
        }
        
        message = json.dumps(payload)
        
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"Failed to send WS message, marking disconnected: {e}")
                disconnected.add(connection)
                
        # Cleanup broken connections
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()
