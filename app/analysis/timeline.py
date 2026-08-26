"""时间线构建：按发布时间排序关键事件。"""

from __future__ import annotations

import time

from app.analysis.models import TimelineEvent
from app.services.collector import SourceItem


def analyze(items: list[SourceItem]) -> list[TimelineEvent]:
    """按发布时间升序排列关键事件。

    无发布时间的来源（如 Tavily/知乎热榜）以采集时间为兜底，
    保证真实数据源也能进入时间线。
    """
    now = time.time()
    events = [
        TimelineEvent(ts=it.published_at if it.published_at is not None else now, title=it.title)
        for it in items
    ]
    events.sort(key=lambda e: e.ts)
    return events
