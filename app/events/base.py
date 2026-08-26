"""领域事件模型与 EventBus 接口（契约，冻结）。"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Protocol


class EventType:
    """实时消息类型（对应需求 2.2.10）。"""

    APP_STATUS = "app_status"
    APP_OUTPUT = "app_output"
    FORUM_LOG = "forum_log"
    SYSTEM_STATUS = "system_status"
    GRAPH_READY = "graph_ready"
    ERROR = "error"


@dataclass(frozen=True)
class DomainEvent:
    """领域事件，payload 依 type 而定。"""

    type: str
    payload: dict[str, Any]
    ts: float = field(default_factory=time.time)


EventHandler = Callable[[DomainEvent], None]


class EventBus(Protocol):
    """事件总线接口：发布/订阅，用于跨模块解耦。"""

    def publish(self, event: DomainEvent) -> None: ...

    def subscribe(self, event_type: str, handler: EventHandler) -> None: ...
