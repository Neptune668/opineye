"""配置接口：读取、更新（热更新）。"""
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ApiResponse, ConfigData
from app.services import config_service

router = APIRouter(tags=["config"])


@router.get("/api/config")
async def get_config():
    config = config_service.get_config()
    return ApiResponse(data=ConfigData(config=config))


@router.post("/api/config")
async def update_config(req: ConfigData):
    config = config_service.update_config(req.config)
    return ApiResponse(data=ConfigData(config=config))
