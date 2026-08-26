"""配置模块路由：GET/POST /api/config。"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends

from app.dependencies import get_config_service
from app.services.config_service import ConfigService

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config")
def get_config(svc: ConfigService = Depends(get_config_service)) -> dict:
    cfg = svc.read()
    return {"code": 0, "message": "success", "data": cfg.data}


@router.post("/config")
def update_config(
    payload: dict[str, Any] = Body(...),
    svc: ConfigService = Depends(get_config_service),
) -> dict:
    expected_version = int(payload.pop("version", 0))
    cfg = svc.save(payload, expected_version)
    return {"code": 0, "message": "success", "data": cfg.data}
