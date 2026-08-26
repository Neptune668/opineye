"""单功能应用占位任务（T4）。

任务体为空占位，仅用于验证 ProcessManager 的启停/状态/撤销闭环。
真实采集与分析逻辑在 T6（采集）、T7（检索分析）中注入。
"""

from __future__ import annotations

from app.tasks.celery_app import celery_app


@celery_app.task(name="opineye.placeholder")
def placeholder_task(app_name: str) -> str:
    """占位任务：模拟一个可被启动/撤销的长任务。"""
    return f"placeholder completed: {app_name}"
