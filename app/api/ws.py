"""WebSocket 实时消息端点：/ws。"""

from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.dependencies import get_connection_manager
from app.services.ws_manager import ConnectionManager

router = APIRouter(tags=["ws"])


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    manager: ConnectionManager = get_connection_manager()
    await manager.connect(websocket)
    try:
        while True:
            # 保持连接，忽略客户端消息（当前为服务端单向推送）
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
