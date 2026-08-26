"""时间线构建：按发布时间排序关键事件。"""

from __future__ import annotations

from app.analysis.models import TimelineEvent
from app.services.collector import SourceItem


def analyze(items: list[SourceItem]) -> list[TimelineEvent]:
    """提取有发布时间的来源，按时间升序排列。"""
    events = [
        TimelineEvent(ts=it.published_at, title=it.title)
        for it in items
        if it.published_at is not None
    ]
    events.sort(key=lambda e: e.ts)
    return events
