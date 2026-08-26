"""系统启停路由：/api/system/status、/start、/shutdown。

权限：status 允许 user 及以上；start/shutdown 仅 root。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_admin, require_user
from app.dependencies import get_system_service
from app.services.system_service import SystemService

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def status(
    svc: SystemService = Depends(get_system_service),
    _: object = Depends(require_user),
) -> dict:
    return {"code": 0, "message": "success", "data": {"system_status": svc.status().value}}


@router.post("/start")
def start(
    svc: SystemService = Depends(get_system_service),
    _: object = Depends(require_admin),
) -> dict:
    state = svc.start()
    return {"code": 0, "message": "success", "data": {"system_status": state.value}}


@router.post("/shutdown")
def shutdown(
    svc: SystemService = Depends(get_system_service),
    _: object = Depends(require_admin),
) -> dict:
    state = svc.shutdown()
    return {"code": 0, "message": "success", "data": {"system_status": state.value}}
