"""依赖装配层：统一组装各模块依赖，供 FastAPI Depends 使用。

后续任务（T3 配置、T4 进程管理等）在此注册其接口的默认实现。
"""

from __future__ import annotations

from functools import lru_cache

from app.events.base import EventBus
from app.events.memory_bus import MemoryEventBus
from app.services.config_service import ConfigService, JsonConfigService
from app.services.process_manager import InMemoryProcessManager, ProcessManager
from app.tasks.registry import AppRegistry


@lru_cache
def get_event_bus() -> EventBus:
    """返回进程内单例事件总线（T1 交付）。"""
    return MemoryEventBus()


@lru_cache
def get_config_service() -> ConfigService:
    """返回进程内单例配置服务（T3 交付）。"""
    return JsonConfigService()


@lru_cache
def get_app_registry() -> AppRegistry:
    """返回应用注册表单例（T4 交付）。"""
    return AppRegistry()


@lru_cache
def get_process_manager() -> ProcessManager:
    """返回进程内单例进程管理器（T4 交付，内存实现）。"""
    return InMemoryProcessManager(registry=get_app_registry(), event_bus=get_event_bus())
