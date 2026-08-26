"""依赖装配层：统一组装各模块依赖，供 FastAPI Depends 使用。

后续任务（T3 配置、T4 进程管理等）在此注册其接口的默认实现。
"""

from __future__ import annotations

from functools import lru_cache

from app.config import settings
from app.events.base import EventBus
from app.events.memory_bus import MemoryEventBus
from app.analysis.llm import build_llm_client
from app.services.collector import (
    Collector,
    CompositeCollector,
    DataSourceCollector,
    InternalDataCollector,
)
from app.services.config_service import ConfigService, JsonConfigService
from app.services.datasource import build_datasource
from app.services.forum_service import ForumCollector, ZhihuForumCollector
from app.services.graph_service import FileGraphStore
from app.services.output_service import AppOutputReader, FileAppOutputReader
from app.services.process_manager import InMemoryProcessManager, ProcessManager
from app.services.report_service import MarkdownReportWriter, ReportWriter
from app.services.search_service import RuleSearchEngine, SearchEngine
from app.services.system_service import InMemorySystemService, SystemService
from app.services.ws_manager import ConnectionManager
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


def _build_collectors(ds_configs: dict) -> dict[str, Collector]:
    """根据数据源配置构建各来源采集器映射。"""
    collectors: dict[str, Collector] = {
        SourceType.INTERNAL_DATA.value: InternalDataCollector(),
    }
    for source_type in (SourceType.NEWS, SourceType.IMAGE, SourceType.VIDEO, SourceType.FORUM_POST):
        ds_cfg = ds_configs.get(source_type.value, {"type": "file", "path": f"data/{source_type.value}.json"})
        collectors[source_type.value] = DataSourceCollector(
            source_type.value, build_datasource(ds_cfg)
        )
    return collectors


@lru_cache
def get_collector() -> Collector:
    """返回组合采集器（T6 交付）。

    internal_data 为真实离线采集；news/image/video/forum_post
    通过可插拔数据源适配器（默认 file 类型）采集。

    注册 datasources 配置 watcher，配置保存后热更新采集器映射。
    """
    ds_configs = get_config_service().read().data.get("datasources", {})
    composite = CompositeCollector(_build_collectors(ds_configs))
    get_config_service().watch(
        "datasources", lambda new_ds: composite.refresh(_build_collectors(new_ds))
    )
    return composite


@lru_cache
def get_report_writer() -> ReportWriter:
    """返回报告生成器（T8 交付）。"""
    return MarkdownReportWriter()


@lru_cache
def get_graph_store() -> FileGraphStore:
    """返回图谱存储（T10 交付）。"""
    return FileGraphStore()


@lru_cache
def get_search_engine() -> SearchEngine:
    """返回检索分析引擎（T7 交付，规则模式，T12 可选 LLM 增强）。"""
    return RuleSearchEngine(
        collector=get_collector(),
        report_writer=get_report_writer(),
        graph_store=get_graph_store(),
        llm_client=build_llm_client(),
        event_bus=get_event_bus(),
    )


@lru_cache
def get_forum_collector() -> ForumCollector:
    """返回论坛采集器（T9 交付，知乎热榜真实实现，降级 file 数据源）。"""
    config = get_config_service().read().data
    poll_interval = float(config.get("forum", {}).get("poll_interval_seconds", 10))
    forum_cfg = config.get("datasources", {}).get("forum_post", {})
    return ZhihuForumCollector(
        poll_interval=poll_interval,
        max_results=int(forum_cfg.get("max_results", 20)),
        z_c0=settings.z_c0,
    )


@lru_cache
def get_system_service() -> SystemService:
    """返回系统启停服务（T11 交付）。"""
    return InMemorySystemService(process_manager=get_process_manager(), event_bus=get_event_bus())


@lru_cache
def get_connection_manager() -> ConnectionManager:
    """返回 WebSocket 连接管理器（T11 交付）。"""
    return ConnectionManager(event_bus=get_event_bus())
