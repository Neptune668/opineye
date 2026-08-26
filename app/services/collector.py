"""数据采集模块：Collector 接口与各来源采集器实现。

来源类型（对应需求 2.2.8）：news / image / video / forum_post / internal_data。

当前实现策略：
  - internal_data：真实离线采集（读取 data/ 目录预置样本）。
  - news / image / video / forum_post：占位适配器（返回空结果），
    见《未实现功能说明.md》。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.utils.constants import SourceType
from app.utils.logging import get_logger
from app.utils.storage import PROJECT_ROOT

logger = get_logger(__name__)

DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class SourceItem:
    """采集来源条目（契约，冻结）。"""

    source_type: str
    title: str
    url: str | None = None
    summary: str | None = None
    published_at: float | None = None  # epoch 秒


@dataclass(frozen=True)
class CollectRequest:
    """采集请求。"""

    query: str
    source_types: list[str]


class Collector(Protocol):
    """采集器接口（契约，冻结）。"""

    def collect(self, request: CollectRequest) -> list[SourceItem]: ...


class InternalDataCollector:
    """内部数据源采集器：读取 data/ 目录下的样本 JSON 文件。

    数据文件约定：data/{source_type}.json 或 data/internal_data.json，
    结构为 SourceItem 列表。按 query 做标题/摘要的简单关键词匹配过滤。
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


class PlaceholderCollector:
    """占位采集器：news / image / video / forum_post 均返回空结果。

    TODO(placeholder): 后续接入真实数据源替换，见《未实现功能说明.md》2.1。
    """

    def __init__(self, source_type: str) -> None:
        self._source_type = source_type

    def collect(self, request: CollectRequest) -> list[SourceItem]:
        logger.info("占位采集器执行", extra={"source_type": self._source_type, "query": request.query})
        return []


class CompositeCollector:
    """组合采集器：按 source_types 分发到对应采集器并汇总。"""

    def __init__(self, collectors: dict[str, Collector]) -> None:
        self._collectors = collectors

    def collect(self, request: CollectRequest) -> list[SourceItem]:
        result: list[SourceItem] = []
        for st in request.source_types:
            collector = self._collectors.get(st)
            if collector is None:
                logger.warning("未知来源类型", extra={"source_type": st})
                continue
            try:
                result.extend(collector.collect(request))
            except Exception:  # noqa: BLE001 - 单来源失败不影响其他来源
                logger.exception("来源采集失败", extra={"source_type": st})
        return result
