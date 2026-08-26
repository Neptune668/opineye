"""WebSocket 连接管理与事件订阅器。

订阅 EventBus 全部事件，转发给所有已连接客户端。
消息格式统一：{type, payload}，客户端按 type 自行过滤（方案 A）。
"""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import WebSocket

from app.events.base import DomainEvent, EventBus
from app.utils.logging import get_logger

logger = get_logger(__name__)

# 订阅的事件类型（对应需求 2.2.10 六类实时消息）
SUBSCRIBED_TYPES = [
    "app_status",
    "app_output",
    "forum_log",
    "system_status",
    "graph_ready",
    "error",
]


class ConnectionManager:
    """维护活跃 WebSocket 连接，广播事件。"""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()
        self._subscribed = False

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        self._ensure_subscribed()
        logger.info("WebSocket 客户端已连接", extra={"total": len(self._connections)})

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._connections.discard(websocket)
        logger.info("WebSocket 客户端已断开", extra={"total": len(self._connections)})

    async def broadcast(self, message: dict[str, Any]) -> None:
        async with self._lock:
            connections = list(self._connections)
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:  # noqa: BLE001 - 单个连接异常不影响其他
                await self.disconnect(ws)

    def _ensure_subscribed(self) -> None:
        """首次连接时订阅事件总线，避免重复订阅。"""
        if self._subscribed:
            return
        self._subscribed = True
        for event_type in SUBSCRIBED_TYPES:
            self._event_bus.subscribe(event_type, self._make_handler())

    def _make_handler(self):
        """构造事件处理回调（将同步事件转为异步广播）。"""

        def handler(event: DomainEvent) -> None:
            asyncio.create_task(
                self.broadcast({"type": event.type, "payload": event.payload})
            )

        return handler
