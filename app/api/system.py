"""系统启停路由：/api/system/status、/start、/shutdown。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_system_service
from app.services.system_service import SystemService

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/status")
def status(svc: SystemService = Depends(get_system_service)) -> dict:
    return {"code": 0, "message": "success", "data": {"system_status": svc.status().value}}


@router.post("/start")
def start(svc: SystemService = Depends(get_system_service)) -> dict:
    state = svc.start()
    return {"code": 0, "message": "success", "data": {"system_status": state.value}}


@router.post("/shutdown")
def shutdown(svc: SystemService = Depends(get_system_service)) -> dict:
    state = svc.shutdown()
    return {"code": 0, "message": "success", "data": {"system_status": state.value}}
