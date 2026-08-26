"""WebSocket 连接管理与广播。

维护连接集合，提供 connect/disconnect/broadcast，并支持心跳检测：
服务端每 30 秒发送 heartbeat，60 秒无 heartbeat_ack 则主动断开。
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

# 心跳间隔（秒）
HEARTBEAT_INTERVAL = 30
# 心跳超时（秒），超时未收到 ack 则断开
HEARTBEAT_TIMEOUT = 60


class WebSocketManager:
    """WebSocket 连接集合管理。"""

    def __init__(self):
        self._connections: set[WebSocket] = set()
        self._last_ack: dict[WebSocket, float] = {}

    async def connect(self, websocket: WebSocket) -> None:
        """接受连接并注册。"""
        await websocket.accept()
        self._connections.add(websocket)
        self._last_ack[websocket] = time.time()
        logger.info("WebSocket 已连接，当前连接数 %d", len(self._connections))

    def disconnect(self, websocket: WebSocket) -> None:
        """移除连接。"""
        self._connections.discard(websocket)
        self._last_ack.pop(websocket, None)

    async def broadcast(self, message: dict[str, Any]) -> None:  # noqa: ARG002
        """向所有连接广播消息（带统一信封 ts）。"""
        if not self._connections:
            return
        envelope = {"ts": int(time.time() * 1000), **message}
        dead: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_json(envelope)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    def ack(self, websocket: WebSocket) -> None:
        """记录心跳 ack 时间。"""
        self._last_ack[websocket] = time.time()

    def check_timeout(self) -> list[WebSocket]:
        """返回心跳超时连接列表。"""
        now = time.time()
        return [
            ws
            for ws, last in self._last_ack.items()
            if now - last > HEARTBEAT_TIMEOUT
        ]

    async def heartbeat_loop(self) -> None:
        """心跳循环：定时发送 heartbeat，清理超时连接。"""
        while True:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            # 清理超时连接
            for ws in self.check_timeout():
                logger.warning("WebSocket 心跳超时，断开连接")
                try:
                    await ws.close()
                except Exception:
                    pass
                self.disconnect(ws)
            # 发送心跳
            if self._connections:
                await self.broadcast({"type": "heartbeat"})


# 全局单例
ws_manager = WebSocketManager()
