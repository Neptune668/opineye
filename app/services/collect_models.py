"""采集相关数据模型（契约，冻结）。

独立存放 SourceItem 与 CollectRequest，避免 collector 与 datasource 之间的循环导入。
"""

from __future__ import annotations

from dataclasses import dataclass


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
