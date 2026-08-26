"""FastAPI 应用入口。

T1 阶段：启动服务、统一响应与异常处理、健康检查。
后续任务在此挂载各业务路由。
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.exceptions import AppError
from app.utils.logging import get_logger
from app.utils.storage import ensure_dirs

logger = get_logger(__name__)

app = FastAPI(title="opineye", version=__version__)


@app.on_event("startup")
def _startup() -> None:
    ensure_dirs()
    logger.info("应用启动", extra={"version": __version__})


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """业务异常统一响应。"""
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.get("/api/health")
def health() -> dict:
    """健康检查。"""
    return {"code": 0, "message": "success", "data": {"status": "ok"}}
