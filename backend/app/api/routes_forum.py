"""论坛接口：采集启停、日志、历史查询。"""
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ApiResponse, ForumHistoryRequest
from app.services import forum_service

router = APIRouter(tags=["forum"])


@router.get("/api/forum/start")
async def forum_start():
    status = await forum_service.start_collection()
    return ApiResponse(data={"task_status": status})


@router.get("/api/forum/stop")
async def forum_stop():
    status = await forum_service.stop_collection()
    return ApiResponse(data={"task_status": status})


@router.get("/api/forum/log")
async def forum_log(tail: int = 200):
    lines = await forum_service.read_latest_log(tail=tail)
    return ApiResponse(data={"lines": lines})


@router.post("/api/forum/log/history")
async def forum_history(req: ForumHistoryRequest):
    entries = await forum_service.read_history(req.date)
    return ApiResponse(data={"entries": entries})
