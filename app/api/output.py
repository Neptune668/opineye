"""单功能应用输出查看路由：/api/output/{app_name}、/api/test_log/{app_name}。

权限：允许 viewer 及以上。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_viewer
from app.dependencies import get_app_output_reader
from app.services.output_service import AppOutputReader

router = APIRouter(prefix="/api", tags=["output"])


@router.get("/output/{app_name}")
def get_output(
    app_name: str,
    reader: AppOutputReader = Depends(get_app_output_reader),
    _: object = Depends(require_viewer),
) -> dict:
    text = reader.read_output(app_name)
    return {"code": 0, "message": "success", "data": {"app_name": app_name, "output_text": text}}


@router.get("/test_log/{app_name}")
def get_test_log(
    app_name: str,
    tail: int = Query(200, ge=1, le=10000),
    reader: AppOutputReader = Depends(get_app_output_reader),
    _: object = Depends(require_viewer),
) -> dict:
    lines = reader.read_log(app_name, tail=tail)
    return {"code": 0, "message": "success", "data": {"app_name": app_name, "lines": lines}}
