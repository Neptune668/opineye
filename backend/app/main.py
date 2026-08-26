"""FastAPI 应用入口。

挂载路由、全局异常处理、CORS，并在启动时初始化数据目录。
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.store import ensure_data_dirs
from app.api.routes_status import router as status_router

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动时初始化数据目录与默认配置。"""
    ensure_data_dirs()
    logger.info("舆情分析平台后端已启动")
    yield
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
