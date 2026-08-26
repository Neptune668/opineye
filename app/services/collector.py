"""数据采集模块：Collector 接口与各来源采集器实现。

来源类型（对应需求 2.2.8）：news / image / video / forum_post / internal_data。

实现策略：
  - internal_data：真实离线采集（读取 data/ 目录预置样本）。
  - news / image / video / forum_post：通过可插拔数据源适配器采集，
    默认 file 类型（读取本地 JSON），可配置为 http 接入真实数据源。
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Protocol

from app.services.collect_models import CollectRequest, SourceItem
from app.services.datasource import DataSource
from app.utils.constants import SourceType
from app.utils.logging import get_logger
from app.utils.storage import PROJECT_ROOT

logger = get_logger(__name__)

DATA_DIR = PROJECT_ROOT / "data"

# 向后兼容：重新导出数据模型
__all__ = ["SourceItem", "CollectRequest", "Collector", "InternalDataCollector", "DataSourceCollector", "CompositeCollector"]


class Collector(Protocol):
    """采集器接口（契约，冻结）。"""

    def collect(self, request: CollectRequest) -> list[SourceItem]: ...


class InternalDataCollector:
    """内部数据源采集器：读取 data/ 目录下的样本 JSON 文件。

    数据文件约定：data/internal_data.json，结构为 SourceItem 列表。
    按 query 做标题/摘要的简单关键词匹配过滤。
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self._data_dir = data_dir

    def collect(self, request: CollectRequest) -> list[SourceItem]:
        path = self._data_dir / "internal_data.json"
        if not path.exists():
            logger.warning("内部数据源文件不存在", extra={"path": str(path)})
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        items = [self._to_item(x) for x in raw if isinstance(x, dict)]
        # 关键词过滤：query 为空时返回全部
        q = request.query.strip().lower()
        if not q:
            return items
        return [it for it in items if q in it.title.lower() or (it.summary or "").lower().find(q) >= 0]

    @staticmethod
    def _to_item(x: dict) -> SourceItem:
        return SourceItem(
            source_type=x.get("source_type", SourceType.INTERNAL_DATA.value),
            title=x.get("title", ""),
            url=x.get("url"),
            summary=x.get("summary"),
            published_at=x.get("published_at"),
        )


class DataSourceCollector:
    """基于数据源适配器的采集器。

    将 news / image / video / forum_post 等来源委托给可插拔的 DataSource，
    实现配置化采集。
    """

    def __init__(self, source_type: str, data_source: DataSource) -> None:
        self._source_type = source_type
        self._data_source = data_source

    def collect(self, request: CollectRequest) -> list[SourceItem]:
        try:
            return self._data_source.fetch(request.query)
        except Exception:  # noqa: BLE001 - 采集失败返回空，不影响其他来源
            logger.exception("数据源采集失败", extra={"source_type": self._source_type})
            return []


class CompositeCollector:
    """组合采集器：按 source_types 分发到对应采集器并汇总。

    支持 refresh() 热更新采集器映射，供配置变更后动态替换数据源。
    """

    def __init__(self, collectors: dict[str, Collector]) -> None:
        self._lock = threading.RLock()
        self._collectors = collectors

    def refresh(self, collectors: dict[str, Collector]) -> None:
        """热更新采集器映射（线程安全）。"""
        with self._lock:
            self._collectors = collectors

    def collect(self, request: CollectRequest) -> list[SourceItem]:
        with self._lock:
            collectors = self._collectors
        result: list[SourceItem] = []
        for st in request.source_types:
            collector = collectors.get(st)
            if collector is None:
                logger.warning("未知来源类型", extra={"source_type": st})
                continue
            try:
                result.extend(collector.collect(request))
            except Exception:  # noqa: BLE001 - 单来源失败不影响其他来源
                logger.exception("来源采集失败", extra={"source_type": st})
        return result
