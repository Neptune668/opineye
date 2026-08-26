"""Pydantic 请求/响应模型。

统一响应结构：{ code, message, data }
"""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应包装。"""

    code: int = 0
    message: str = "ok"
    data: T | None = None


# ---- 状态相关响应模型 ----


class AppStatusData(BaseModel):
    app_name: str
    status: str


class StatusData(BaseModel):
    system_status: str
    apps: dict[str, str]


class OutputData(BaseModel):
    app_name: str
    output_text: str


class TestLogData(BaseModel):
    app_name: str
    lines: list[str]


# ---- 检索相关请求/响应模型 ----


class SearchRequest(BaseModel):
    query: str
    source_types: list[str]


class SearchResult(BaseModel):
    report_id: str
    report_md: str
    graph_path: str


# ---- 图谱查询请求 ----


class GraphQueryRequest(BaseModel):
    report_id: str | None = None
    node: str | None = None
    relation: str | None = None


# ---- 论坛历史日志请求 ----


class ForumHistoryRequest(BaseModel):
    date: str


# ---- 配置相关 ----


class ConfigData(BaseModel):
    config: dict[str, Any]
