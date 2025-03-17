from fastapi import WebSocket
from typing import Dict
from core.logger import logger

class WebSocketManager:
    """Manage all the websocket connections in the app"""
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    async def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].close()
            del self.active_connections[user_id]

    async def send_message(self, user_id: str, message: str):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending message by ws to user: {user_id}, probably the user is not connected. {e}")
                if self.active_connections.get(user_id) is not None:
                    del self.active_connections[user_id]
    
    async def broadcast(self, message: str):
        for websocket in self.active_connections.values():
            await websocket.send_text(message)

ws_manager = WebSocketManager()
