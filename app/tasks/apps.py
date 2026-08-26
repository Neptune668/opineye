"""单功能应用真实任务体（T4 + T6/T7 整合）。

将各单功能应用绑定到真实任务：
  - topic_search：主题检索（采集 + 分析 + 报告 + 图谱）
  - media_search：多媒体检索（采集 image/video 来源）
  - forum_collect：论坛采集
  - insight：洞察分析
  - report：报告生成
  - graph：图谱查询

每个任务可被 ProcessManager 启动/停止。
"""

from __future__ import annotations

from app.tasks.celery_app import celery_app


@celery_app.task(name="opineye.topic_search")
def topic_search_task(query: str, source_types: list[str]) -> dict:
    """主题检索任务：采集 + 分析 + 报告 + 图谱。"""
    from app.dependencies import get_search_engine
    from app.services.search_service import SearchRequest

    result = get_search_engine().search(SearchRequest(query=query, source_types=source_types))
    return {
        "task_id": result.task_id,
        "report_id": result.report.report_id,
        "sources": len(result.sources),
        "sentiment": result.analysis.sentiment.overall,
    }


@celery_app.task(name="opineye.media_search")
def media_search_task(query: str) -> dict:
    """多媒体检索任务：采集 image/video 来源。"""
    from app.dependencies import get_collector
    from app.services.collector import CollectRequest

    items = get_collector().collect(
        CollectRequest(query=query, source_types=["image", "video"])
    )
    return {"query": query, "count": len(items)}


@celery_app.task(name="opineye.forum_collect")
def forum_collect_task() -> dict:
    """论坛采集任务：启动论坛采集器。"""
    from app.dependencies import get_forum_collector

    get_forum_collector().start()
    return {"status": "started"}


@celery_app.task(name="opineye.insight")
def insight_task(query: str) -> dict:
    """洞察分析任务：对主题做洞察分析（复用检索引擎的分析能力）。"""
    from app.dependencies import get_search_engine
    from app.services.search_service import SearchRequest

    result = get_search_engine().search(
        SearchRequest(query=query, source_types=["internal_data"])
    )
    return {
        "overview": result.analysis.overview,
        "risks": result.analysis.risks,
        "viewpoints": result.analysis.viewpoints,
    }


@celery_app.task(name="opineye.report")
def report_task(report_id: str) -> dict:
    """报告生成任务：按 report_id 定位报告文件。"""
    from app.utils.storage import REPORTS_DIR

    path = REPORTS_DIR / report_id / "report.md"
    return {"report_id": report_id, "exists": path.exists(), "path": str(path)}


@celery_app.task(name="opineye.graph")
def graph_task(report_id: str) -> dict:
    """图谱查询任务：按 report_id 加载图谱。"""
    from app.dependencies import get_graph_store

    graph = get_graph_store().load(report_id)
    return {"report_id": report_id, "nodes": len(graph.nodes), "edges": len(graph.edges)}


# 占位任务（保留兼容，避免旧注册表引用报错）
@celery_app.task(name="opineye.placeholder")
def placeholder_task(app_name: str) -> str:
    """占位任务：兼容保留。"""
    return f"placeholder completed: {app_name}"
