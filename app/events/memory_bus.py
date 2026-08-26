"""内存事件总线实现（T1 交付的默认实现，单进程内解耦）。"""

from __future__ import annotations

import threading
from collections import defaultdict

from app.events.base import DomainEvent, EventBus, EventHandler
from app.utils.logging import get_logger

logger = get_logger(__name__)


class MemoryEventBus:
    """基于进程内订阅表的事件总线，线程安全。"""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = threading.Lock()

    def publish(self, event: DomainEvent) -> None:
        with self._lock:
            handlers = list(self._handlers.get(event.type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001 - 订阅方异常不应中断发布
                logger.exception("事件处理异常 event_type=%s", event.type)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        with self._lock:
            self._handlers[event_type].append(handler)
