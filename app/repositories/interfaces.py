"""仓储接口定义（契约，冻结）。

对应文档 4.8 节。Service 层依赖这些接口而非 ORM 会话，
便于用内存实现做单元测试。
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.models.forum import ForumLog
from app.models.graph import GraphEdge, GraphNode
from app.models.report import Report
from app.models.search import SearchTask, Source


class SearchTaskRepository(Protocol):
    def create(self, task: SearchTask) -> SearchTask: ...

    def get(self, task_id: str) -> SearchTask | None: ...

    def update_status(self, task_id: str, status: str, error: str | None = None) -> None: ...


class SourceRepository(Protocol):
    def bulk_insert(self, sources: list[Source]) -> None: ...

    def list_by_task(self, task_id: str) -> list[Source]: ...


class ReportRepository(Protocol):
    def create(self, report: Report) -> Report: ...

    def get_by_report_id(self, report_id: str) -> Report | None: ...


class GraphRepository(Protocol):
    def save_nodes(self, report_id: str, nodes: list[GraphNode]) -> None: ...

    def save_edges(self, report_id: str, edges: list[GraphEdge]) -> None: ...

    def query(self, report_id: str, cond: dict) -> dict: ...


class ForumLogRepository(Protocol):
    def append(self, entry: ForumLog) -> None: ...

    def query_by_date(self, date: datetime) -> list[ForumLog]: ...
