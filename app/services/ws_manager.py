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
        self._loop: asyncio.AbstractEventLoop | None = None

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections.add(websocket)
        # 记录主事件循环，供同步上下文跨线程调度广播
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
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
        """构造事件处理回调（将同步事件安全地调度到主事件循环广播）。

        事件发布发生在同步上下文（FastAPI 同步路由的线程池线程），
        因此不能用 asyncio.create_task；改用 run_coroutine_threadsafe。
        """

        def handler(event: DomainEvent) -> None:
            loop = self._loop
            if loop is None:
                # 尚未有 WebSocket 连接（无事件循环），忽略
                return
            future = asyncio.run_coroutine_threadsafe(
                self.broadcast({"type": event.type, "payload": event.payload}), loop
            )
            try:
                future.result(timeout=5)
            except Exception:  # noqa: BLE001 - 广播失败不影响主流程
                logger.exception("WebSocket 广播异常", extra={"event_type": event.type})

        return handler
