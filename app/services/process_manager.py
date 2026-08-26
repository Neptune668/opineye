"""进程管理模块：ProcessManager 接口与内存实现。

职责：单功能应用启动、停止、状态采集。聚焦生命周期单一职责；
输出采集（T5）与真实任务逻辑（T6/T7）不在此模块。

状态存储：当前为进程内存实现（InMemoryProcessManager），
后续通过同一接口切换 Redis 实现，调用方无需改动。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Protocol

from app.events.base import DomainEvent, EventBus, EventType
from app.exceptions import InvalidStateError, NotFoundError
from app.tasks.registry import AppRegistry
from app.utils.constants import AppState
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class AppStatus:
    """应用状态快照。"""

    app_name: str
    status: AppState
    last_error: str | None = None


class ProcessManager(Protocol):
    """进程管理接口（契约，冻结）。"""

    def start(self, app_name: str) -> AppStatus: ...

    def stop(self, app_name: str) -> AppStatus: ...

    def status(self, app_name: str | None = None) -> dict[str, AppStatus]: ...


class InMemoryProcessManager:
    """基于进程内存状态存储的进程管理实现。

    线程安全；状态机流转遵循文档 T4 设计的状态流转表。
    """

    # 合法状态流转表（当前状态 -> 允许的目标状态集合）
    _TRANSITIONS: dict[AppState, set[AppState]] = {
        AppState.STOPPED: {AppState.STARTING},
        AppState.STARTING: {AppState.RUNNING, AppState.FAILED},
        AppState.RUNNING: {AppState.STOPPING, AppState.STOPPED, AppState.FAILED},
        AppState.STOPPING: {AppState.STOPPED},
        AppState.FAILED: {AppState.STARTING},
    }

    def __init__(self, registry: AppRegistry, event_bus: EventBus) -> None:
        self._registry = registry
        self._event_bus = event_bus
        self._lock = threading.RLock()
        self._states: dict[str, AppStatus] = {}

    # ---- 对外接口 ----

    def start(self, app_name: str) -> AppStatus:
        with self._lock:
            if app_name not in self._registry:
                raise NotFoundError(f"应用不存在：{app_name}")

            current = self._states.get(app_name, AppStatus(app_name, AppState.STOPPED))

            if current.status in (AppState.STARTING, AppState.RUNNING):
                raise InvalidStateError(f"应用 {app_name} 状态为 {current.status.value}，不允许启动")

            # 启动：立即置 starting（占位任务，无需真正下发）
            self._set(app_name, AppState.STARTING)
            # 占位任务直接模拟运行中（真实逻辑在 T6/T7 中由 Worker 上报）
            self._set(app_name, AppState.RUNNING)
            return self._states[app_name]

    def stop(self, app_name: str) -> AppStatus:
        with self._lock:
            if app_name not in self._registry:
                raise NotFoundError(f"应用不存在：{app_name}")

            current = self._states.get(app_name, AppStatus(app_name, AppState.STOPPED))

            if current.status in (AppState.STOPPED, AppState.FAILED):
                # 幂等：已停止/已失败直接返回当前状态
                return current

            self._set(app_name, AppState.STOPPING)
            self._set(app_name, AppState.STOPPED)
            return self._states[app_name]

    def status(self, app_name: str | None = None) -> dict[str, AppStatus]:
        with self._lock:
            if app_name is not None:
                if app_name not in self._registry:
                    raise NotFoundError(f"应用不存在：{app_name}")
                st = self._states.get(app_name, AppStatus(app_name, AppState.STOPPED))
                return {app_name: st}
            # 返回全部注册应用的当前状态
            result: dict[str, AppStatus] = {}
            for name in self._registry.names():
                result[name] = self._states.get(name, AppStatus(name, AppState.STOPPED))
            return result

    # ---- 内部 ----

    def _set(self, app_name: str, new_state: AppState, error: str | None = None) -> None:
        current = self._states.get(app_name, AppStatus(app_name, AppState.STOPPED))
        if current.status == new_state:
            return
        # 校验流转合法性（兜底保护）
        if new_state not in self._TRANSITIONS.get(current.status, set()):
            logger.warning(
                "非法状态流转",
                extra={"app": app_name, "from": current.status.value, "to": new_state.value},
            )
        self._states[app_name] = AppStatus(app_name, new_state, error)
        self._event_bus.publish(
            DomainEvent(type=EventType.APP_STATUS, payload={"app_name": app_name, "status": new_state.value})
        )
        logger.info("应用状态变更", extra={"app": app_name, "status": new_state.value})
