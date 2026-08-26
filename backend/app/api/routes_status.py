"""状态接口：应用启停、状态、输出、日志查询。

统一前缀 /api，返回结构 { code, message, data }。
"""
from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException

from app.core.process_manager import process_manager
from app.models.schemas import (
    ApiResponse,
    AppStatusData,
    OutputData,
    StatusData,
    TestLogData,
)

router = APIRouter(tags=["status"])

APP_NAME_PATTERN = re.compile(r"^[a-z_]+$")


def _validate_app_name(app_name: str) -> str:
    """校验应用名合法性，非法则抛出 422。"""
    if not APP_NAME_PATTERN.match(app_name):
        raise HTTPException(
            status_code=422,
            detail=f"非法应用名：{app_name}，仅允许小写字母与下划线",
        )
    return app_name


@router.get("/api/status", response_model=ApiResponse[StatusData])
async def get_status() -> ApiResponse[StatusData]:
    """控制台状态 + 各应用状态。"""
    apps = process_manager.all_status()
    return ApiResponse(
        data=StatusData(system_status="online", apps=apps)
    )


@router.get("/api/start/{app_name}", response_model=ApiResponse[AppStatusData])
async def start_app(app_name: str) -> ApiResponse[AppStatusData]:
    """启动单功能应用。"""
    app_name = _validate_app_name(app_name)
    ok = await process_manager.start(app_name)
    if not ok:
        raise HTTPException(status_code=409, detail=f"应用 {app_name} 启动失败或已运行")
    return ApiResponse(
        data=AppStatusData(app_name=app_name, status=process_manager.status(app_name))
    )


@router.get("/api/stop/{app_name}", response_model=ApiResponse[AppStatusData])
async def stop_app(app_name: str) -> ApiResponse[AppStatusData]:
    """停止单功能应用。"""
    app_name = _validate_app_name(app_name)
    await process_manager.stop(app_name)
    return ApiResponse(
        data=AppStatusData(app_name=app_name, status=process_manager.status(app_name))
    )


@router.get("/api/output/{app_name}", response_model=ApiResponse[OutputData])
async def get_output(app_name: str) -> ApiResponse[OutputData]:
    """应用最近输出。"""
    app_name = _validate_app_name(app_name)
    text = await process_manager.read_output(app_name)
    return ApiResponse(data=OutputData(app_name=app_name, output_text=text))


@router.get("/api/test_log/{app_name}", response_model=ApiResponse[TestLogData])
async def get_test_log(app_name: str, tail: int = 200) -> ApiResponse[TestLogData]:
    """应用测试日志（尾部）。"""
    app_name = _validate_app_name(app_name)
    lines = await process_manager.read_log(app_name, tail=tail)
    return ApiResponse(data=TestLogData(app_name=app_name, lines=lines))
