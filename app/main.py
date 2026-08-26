"""FastAPI 应用入口。

T1 阶段：启动服务、统一响应与异常处理、健康检查。
后续任务在此挂载各业务路由。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import __version__
from app.api import apps as apps_api
from app.api import auth as auth_api
from app.api import config as config_api
from app.api import forum as forum_api
from app.api import graph as graph_api
from app.api import output as output_api
from app.api import search as search_api
from app.api import system as system_api
from app.api import ws as ws_api
from app.config import settings
from app.exceptions import AppError
from app.utils.logging import get_logger
from app.utils.storage import ensure_dirs

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """应用生命周期：初始化目录、内置管理员，并校验安全配置。"""
    ensure_dirs()

    if settings.secret_key == "change-me":
        logger.warning("SECRET_KEY 仍为默认值，生产环境请务必修改")

    # 初始化内置 admin 管理员（若不存在）
    try:
        from app.services.user_init import ensure_root_user

        ensure_root_user()
    except Exception:  # noqa: BLE001 - admin 初始化失败不阻断启动
        logger.exception("admin 管理员初始化失败")

    logger.info("应用启动", extra={"version": __version__})
    yield


app = FastAPI(title="opineye", version=__version__, lifespan=lifespan)

app.include_router(auth_api.router)
app.include_router(config_api.router)
app.include_router(apps_api.router)
app.include_router(output_api.router)
app.include_router(search_api.router)
app.include_router(forum_api.router)
app.include_router(graph_api.router)
app.include_router(system_api.router)
app.include_router(ws_api.router)

# 静态文件与前端页面
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index() -> FileResponse:
    """控制台首页（前端阶段）。"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/graph-viewer")
def graph_viewer_index() -> FileResponse:
    """图谱查看页（无 report_id，前端加载最新图谱）。"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.get("/graph-viewer/{report_id}")
def graph_viewer_by_report(report_id: str) -> FileResponse:
    """图谱查看页（指定 report_id，前端解析路径并加载对应图谱）。"""
    return FileResponse(str(STATIC_DIR / "index.html"))


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    """业务异常统一响应。"""
    _publish_error("api", exc.message)
    return JSONResponse(
        status_code=exc.http_status,
        content={"code": exc.code, "message": exc.message, "data": None},
    )


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTP 异常统一响应（404/405 等路由级错误）。"""
    code = 1002 if exc.status_code == 404 else 5001
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": code, "message": str(exc.detail), "data": None},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    """未捕获异常兜底，统一返回 500，避免暴露内部细节。"""
    logger.exception("未处理异常", extra={"error": str(exc)})
    _publish_error("system", str(exc))
    return JSONResponse(
        status_code=500,
        content={"code": 5001, "message": "系统内部错误", "data": None},
    )


def _publish_error(module_name: str, error_message: str) -> None:
    """发布 error 事件（G5）。"""
    from app.dependencies import get_event_bus
    from app.events.base import DomainEvent, EventType

    get_event_bus().publish(
        DomainEvent(
            type=EventType.ERROR,
            payload={"module_name": module_name, "error_message": error_message},
        )
    )


@app.get("/api/health")
def health() -> dict:
    """健康检查。"""
    return {"code": 0, "message": "success", "data": {"status": "ok"}}
