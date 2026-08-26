"""系统接口：整体服务状态查询与启停。

系统状态机：offline → starting → online → shutting_down → offline
"""
from __future__ import annotations

import logging

from fastapi import APIRouter

from app.config import get_config
from app.core.process_manager import process_manager
from app.models.schemas import ApiResponse

router = APIRouter(tags=["system"])

logger = logging.getLogger(__name__)

# 系统状态（进程内维护）
_system_status = "online"


def get_system_status() -> str:
    return _system_status


def set_system_status(status: str) -> None:
    global _system_status
    _system_status = status


@router.get("/api/system/status")
async def system_status():
    """整体服务状态 + 运行中应用 + 最近错误。"""
    running_apps = {
        name: status
        for name, status in process_manager.all_status().items()
        if status == "running"
    }
    return ApiResponse(
        data={
            "system_status": get_system_status(),
            "running_apps": running_apps,
            "errors": [],  # 首版暂不持久化错误，后续接入 error 消息汇总
        }
    )


@router.post("/api/system/start")
async def system_start():
    """启动整体服务：默认启动 config.system.default_apps 中的应用。"""
    set_system_status("online")
    config = get_config()
    default_apps = config.get("system", {}).get("default_apps", [])
    started = {}
    for app_name in default_apps:
        await process_manager.start(app_name)
        started[app_name] = process_manager.status(app_name)
    logger.info("系统启动，已启动应用：%s", list(started))
    return ApiResponse(data={"system_status": get_system_status()})


@router.post("/api/system/shutdown")
async def system_shutdown():
    """关闭整体服务：停止全部运行中应用。"""
    set_system_status("shutting_down")
    for app_name in list(process_manager.all_status().keys()):
        await process_manager.stop(app_name)
    set_system_status("offline")
    logger.info("系统已关闭")
    return ApiResponse(data={"system_status": get_system_status()})
