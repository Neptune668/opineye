"""论坛模块路由：/api/forum/start、/stop、/log、/log/history。

权限：start/stop 仅 operator 及以上；log/history 允许 viewer 及以上。
"""

from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter, Depends

from app.api.deps import require_operator, require_viewer
from app.dependencies import get_forum_collector
from app.services.forum_service import ForumCollector

router = APIRouter(prefix="/api/forum", tags=["forum"])


class HistoryBody(BaseModel):
    date: str


def _entries(entries: list) -> list[dict]:
    return [
        {"ts": e.ts, "event_type": e.event_type, "message": e.message, "task_status": e.task_status}
        for e in entries
    ]


@router.get("/start")
def start(
    forum: ForumCollector = Depends(get_forum_collector),
    _: object = Depends(require_operator),
) -> dict:
    forum.start()
    return {"code": 0, "message": "success", "data": {"status": "running"}}


@router.get("/stop")
def stop(
    forum: ForumCollector = Depends(get_forum_collector),
    _: object = Depends(require_operator),
) -> dict:
    forum.stop()
    return {"code": 0, "message": "success", "data": {"status": "stopped"}}


@router.get("/log")
def log(
    forum: ForumCollector = Depends(get_forum_collector),
    _: object = Depends(require_viewer),
) -> dict:
    return {"code": 0, "message": "success", "data": {"entries": _entries(forum.latest_log())}}


@router.post("/log/history")
def history(
    body: HistoryBody,
    forum: ForumCollector = Depends(get_forum_collector),
    _: object = Depends(require_viewer),
) -> dict:
    return {"code": 0, "message": "success", "data": {"entries": _entries(forum.history(body.date))}}
