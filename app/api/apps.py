"""单功能应用启停路由：/api/status、/api/start/{app_name}、/api/stop/{app_name}。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies import get_process_manager
from app.services.process_manager import ProcessManager

router = APIRouter(prefix="/api", tags=["apps"])


def _status_to_dict(st: dict) -> dict:
    return {
        name: {"app_name": s.app_name, "status": s.status.value, "last_error": s.last_error}
        for name, s in st.items()
    }


@router.get("/status")
def get_status(pm: ProcessManager = Depends(get_process_manager)) -> dict:
    st = pm.status()
    return {"code": 0, "message": "success", "data": _status_to_dict(st)}


@router.get("/start/{app_name}")
def start_app(app_name: str, pm: ProcessManager = Depends(get_process_manager)) -> dict:
    st = pm.start(app_name)
    return {
        "code": 0,
        "message": "success",
        "data": {"app_name": st.app_name, "status": st.status.value, "last_error": st.last_error},
    }


@router.get("/stop/{app_name}")
def stop_app(app_name: str, pm: ProcessManager = Depends(get_process_manager)) -> dict:
    st = pm.stop(app_name)
    return {
        "code": 0,
        "message": "success",
        "data": {"app_name": st.app_name, "status": st.status.value, "last_error": st.last_error},
    }
