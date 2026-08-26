"""Celery 应用实例。

T4 阶段：提供单功能应用的异步任务载体。
当前采用任务占位（空任务体），聚焦生命周期闭环；真实采集/分析逻辑由 T6/T7 填充。
"""

from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "opineye",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.apps"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=60,
)
