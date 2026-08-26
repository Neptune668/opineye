"""传播渠道统计：按来源类型计数。"""

from __future__ import annotations

from collections import Counter

from app.services.collector import SourceItem


def analyze(items: list[SourceItem]) -> dict[str, int]:
    """统计各来源类型的数量分布。"""
    return dict(Counter(it.source_type for it in items))
