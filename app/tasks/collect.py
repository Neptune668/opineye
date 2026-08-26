"""数据采集 Celery 任务体（T6）。

将 Collector 采集逻辑绑定为 Celery 任务，供 ProcessManager 启动对应应用时调用。
"""

from __future__ import annotations

from app.services.collector import CollectRequest, Collector
from app.tasks.celery_app import celery_app


@celery_app.task(name="opineye.collect")
def collect_task(query: str, source_types: list[str]) -> dict:
    """采集任务：执行采集并返回结果（序列化为字典）。"""
    from app.dependencies import get_collector

    collector: Collector = get_collector()
    items = collector.collect(CollectRequest(query=query, source_types=source_types))
    return {
        "query": query,
        "count": len(items),
        "sources": [
            {
                "source_type": it.source_type,
                "title": it.title,
                "url": it.url,
                "summary": it.summary,
                "published_at": it.published_at,
            }
            for it in items
        ],
    }
