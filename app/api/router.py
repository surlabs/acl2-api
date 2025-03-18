from fastapi import APIRouter, WebSocket
from containers.router import container_router
from api.websocket_manager import ws_manager
from core.logger import logger
from core.config import settings

router = APIRouter(prefix=f"/{settings.API_VERSION}")

router.include_router(container_router, prefix="/acl2", tags=["acl2"])

@router.websocket("/ws/{user_id}")
async def websocket_connect(websocket: WebSocket, user_id: str):
    await ws_manager.connect(websocket=websocket, user_id=user_id)
    while True:
        data = await websocket.receive_text()
        await ws_manager.send_message(user_id=user_id, message=data)