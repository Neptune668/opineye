"""依赖装配层：统一组装各模块依赖，供 FastAPI Depends 使用。

后续任务（T3 配置、T4 进程管理等）在此注册其接口的默认实现。
"""

from __future__ import annotations

from functools import lru_cache

from app.events.base import EventBus
from app.events.memory_bus import MemoryEventBus
from app.services.collector import (
    Collector,
    CompositeCollector,
    InternalDataCollector,
    PlaceholderCollector,
)
from app.services.config_service import ConfigService, JsonConfigService
from app.services.forum_service import ForumCollector, SimulatedForumCollector
from app.services.output_service import AppOutputReader, FileAppOutputReader
from app.services.process_manager import InMemoryProcessManager, ProcessManager
from app.services.report_service import MarkdownReportWriter, ReportWriter
from app.services.search_service import RuleSearchEngine, SearchEngine
from app.tasks.registry import AppRegistry
from app.utils.constants import SourceType


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


@lru_cache
def get_app_output_reader() -> AppOutputReader:
    """返回进程内单例应用输出读取器（T5 交付）。"""
    return FileAppOutputReader()


@lru_cache
def get_collector() -> Collector:
    """返回组合采集器（T6 交付）。

    internal_data 为真实离线采集，其余来源为占位适配器。
    """
    collectors: dict[str, Collector] = {
        SourceType.INTERNAL_DATA.value: InternalDataCollector(),
        SourceType.NEWS.value: PlaceholderCollector(SourceType.NEWS.value),
        SourceType.IMAGE.value: PlaceholderCollector(SourceType.IMAGE.value),
        SourceType.VIDEO.value: PlaceholderCollector(SourceType.VIDEO.value),
        SourceType.FORUM_POST.value: PlaceholderCollector(SourceType.FORUM_POST.value),
    }
    return CompositeCollector(collectors)


@lru_cache
def get_report_writer() -> ReportWriter:
    """返回报告生成器（T8 交付）。"""
    return MarkdownReportWriter()


@lru_cache
def get_search_engine() -> SearchEngine:
    """返回检索分析引擎（T7 交付，规则模式）。"""
    return RuleSearchEngine(collector=get_collector(), report_writer=get_report_writer())


@lru_cache
def get_forum_collector() -> ForumCollector:
    """返回论坛采集器（T9 交付，模拟实现）。"""
    return SimulatedForumCollector()
