"""论坛模块路由：/api/forum/start、/stop、/log、/log/history。"""

from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter, Depends

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
def start(forum: ForumCollector = Depends(get_forum_collector)) -> dict:
    forum.start()
    return {"code": 0, "message": "success", "data": {"status": "running"}}


@router.get("/stop")
def stop(forum: ForumCollector = Depends(get_forum_collector)) -> dict:
    forum.stop()
    return {"code": 0, "message": "success", "data": {"status": "stopped"}}


@router.get("/log")
def log(forum: ForumCollector = Depends(get_forum_collector)) -> dict:
    return {"code": 0, "message": "success", "data": {"entries": _entries(forum.latest_log())}}


@router.post("/log/history")
def history(body: HistoryBody, forum: ForumCollector = Depends(get_forum_collector)) -> dict:
    return {"code": 0, "message": "success", "data": {"entries": _entries(forum.history(body.date))}}
