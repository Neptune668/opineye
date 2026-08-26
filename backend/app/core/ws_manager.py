"""WebSocket 连接管理与广播。

当前为最小占位实现：提供 connect/disconnect/broadcast 接口，
供 process_manager 在无客户端连接时安全调用。完整实现见 M3。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 连接集合管理。"""

    def __init__(self):
        self._connections: set[Any] = set()

    async def connect(self, websocket: Any) -> None:
        self._connections.add(websocket)

    def disconnect(self, websocket: Any) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict) -> None:
        """向所有连接广播消息。当前占位：仅记录日志。"""
        logger.debug("broadcast: %s", message.get("type"))


# 全局单例
ws_manager = WebSocketManager()
