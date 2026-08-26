"""FastAPI 应用入口。

挂载路由、全局异常处理、CORS，并在启动时初始化数据目录。
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.store import ensure_data_dirs
from app.core.ws_manager import ws_manager
from app.api.routes_status import router as status_router
from app.api.routes_system import router as system_router
from app.api.routes_search import router as search_router
from app.api.routes_forum import router as forum_router
from app.api.routes_graph import router as graph_router
from app.api.routes_config import router as config_router

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

_heartbeat_task: asyncio.Task | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据目录、启动心跳循环。"""
    global _heartbeat_task
    ensure_data_dirs()
    _heartbeat_task = asyncio.create_task(ws_manager.heartbeat_loop())
    logger.info("舆情分析平台后端已启动")
    yield
    if _heartbeat_task:
        _heartbeat_task.cancel()
    logger.info("舆情分析平台后端已关闭")


app = FastAPI(title="舆情分析平台", version="1.0.0", lifespan=lifespan)

# CORS（开发阶段全放通）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载路由
app.include_router(status_router)
app.include_router(system_router)
app.include_router(search_router)
app.include_router(forum_router)
app.include_router(graph_router)
app.include_router(config_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 端点：注册连接，循环处理心跳 ack。"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            import json as _json

            try:
                msg = _json.loads(data)
            except _json.JSONDecodeError:
                continue
            if msg.get("type") == "heartbeat_ack":
                ws_manager.ack(websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """统一异常处理：返回 code=500 + 异常类型名。"""
    logger.exception("未处理异常")
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务内部错误: {type(exc).__name__}",
            "data": None,
        },
    )
