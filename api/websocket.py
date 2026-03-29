import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages to all clients."""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to all connected clients. Drops dead connections silently."""
        if not self.active_connections:
            return
        data = json.dumps(message)
        dead = []
        for ws in self.active_connections:
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


# Singleton shared across the app
manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    Live anomaly alert feed.
    Broadcasts {"type": "anomaly_alert", "frame": N, "timestamp": X, "score": Y, "signals": [...]}
    whenever a new ANOMALY event is saved during video processing.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Keep the connection alive by waiting for any client message (ping / text)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
