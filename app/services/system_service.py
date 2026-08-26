"""系统启停模块：系统状态机与整体服务控制。

状态机：offline → starting → online → shutting_down（需求 2.2.4）。
start 时批量启动默认启用应用，shutdown 时批量停止。
"""

from __future__ import annotations

import threading
from typing import Protocol

from app.events.base import DomainEvent, EventBus, EventType
from app.exceptions import InvalidStateError
from app.services.process_manager import ProcessManager
from app.utils.constants import SystemState
from app.utils.logging import get_logger

logger = get_logger(__name__)


class SystemService(Protocol):
    """系统启停接口（契约，冻结）。"""

    def status(self) -> SystemState: ...

    def start(self) -> SystemState: ...

    def shutdown(self) -> SystemState: ...


class InMemorySystemService:
    """基于内存的系统状态实现，联动进程管理器批量启停应用。"""

    def __init__(
        self,
        process_manager: ProcessManager,
        event_bus: EventBus,
        default_apps: list[str] | None = None,
    ) -> None:
        self._pm = process_manager
        self._event_bus = event_bus
        self._default_apps = default_apps or [
            "topic_search",
            "media_search",
            "forum_collect",
            "insight",
            "report",
            "graph",
        ]
        self._lock = threading.RLock()
        self._state = SystemState.OFFLINE

    def status(self) -> SystemState:
        with self._lock:
            return self._state

    def start(self) -> SystemState:
        with self._lock:
            if self._state == SystemState.ONLINE:
                raise InvalidStateError("系统已在线")
            self._state = SystemState.STARTING
        self._publish(SystemState.STARTING)

        # 批量启动默认启用应用
        for app in self._default_apps:
            try:
                self._pm.start(app)
            except InvalidStateError:
                # 已运行的应用跳过
                pass

        with self._lock:
            self._state = SystemState.ONLINE
        self._publish(SystemState.ONLINE)
        logger.info("系统已启动")
        return self._state

    def shutdown(self) -> SystemState:
        with self._lock:
            if self._state == SystemState.OFFLINE:
                raise InvalidStateError("系统已离线")
            self._state = SystemState.SHUTTING_DOWN
        self._publish(SystemState.SHUTTING_DOWN)

        # 批量停止应用
        for app in self._default_apps:
            try:
                self._pm.stop(app)
            except Exception:  # noqa: BLE001 - 单个停止失败不阻断整体
                logger.exception("停止应用失败", extra={"app": app})

        with self._lock:
            self._state = SystemState.OFFLINE
        self._publish(SystemState.OFFLINE)
        logger.info("系统已关闭")
        return self._state

    def _publish(self, state: SystemState) -> None:
        running = [
            name
            for name, st in self._pm.status().items()
            if st.status.value in ("running", "starting")
        ]
        self._event_bus.publish(
            DomainEvent(
                type=EventType.SYSTEM_STATUS,
                payload={"system_status": state.value, "running_apps": running},
            )
        )
