"""基于 SQLAlchemy 的仓储实现（MySQL）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.forum import ForumLog
from app.models.graph import GraphEdge, GraphNode
from app.models.report import Report
from app.models.search import SearchTask, Source


class SqlSearchTaskRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, task: SearchTask) -> SearchTask:
        self._db.add(task)
        self._db.commit()
        self._db.refresh(task)
        return task

    def get(self, task_id: str) -> SearchTask | None:
        stmt = select(SearchTask).where(SearchTask.task_id == task_id)
        return self._db.scalar(stmt)

    def update_status(self, task_id: str, status: str, error: str | None = None) -> None:
        stmt = select(SearchTask).where(SearchTask.task_id == task_id)
        task = self._db.scalar(stmt)
        if task is None:
            return
        task.status = status
        task.error_msg = error
        self._db.commit()


class SqlSourceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def bulk_insert(self, sources: list[Source]) -> None:
        self._db.add_all(sources)
        self._db.commit()

    def list_by_task(self, task_id: str) -> list[Source]:
        stmt = select(Source).where(Source.task_id == task_id)
        return list(self._db.scalars(stmt))


class SqlReportRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, report: Report) -> Report:
        self._db.add(report)
        self._db.commit()
        self._db.refresh(report)
        return report

    def get_by_report_id(self, report_id: str) -> Report | None:
        stmt = select(Report).where(Report.report_id == report_id)
        return self._db.scalar(stmt)


class SqlGraphRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def save_nodes(self, report_id: str, nodes: list[GraphNode]) -> None:
        self._db.add_all(nodes)
        self._db.commit()

    def save_edges(self, report_id: str, edges: list[GraphEdge]) -> None:
        self._db.add_all(edges)
        self._db.commit()

    def query(self, report_id: str, cond: dict) -> dict:
        nodes_stmt = select(GraphNode).where(GraphNode.report_id == report_id)
        edges_stmt = select(GraphEdge).where(GraphEdge.report_id == report_id)
        return {
            "nodes": list(self._db.scalars(nodes_stmt)),
            "edges": list(self._db.scalars(edges_stmt)),
        }


class SqlForumLogRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def append(self, entry: ForumLog) -> None:
        self._db.add(entry)
        self._db.commit()

    def query_by_date(self, date: datetime) -> list[ForumLog]:
        start = datetime(date.year, date.month, date.day)
        end = datetime(date.year, date.month, date.day, 23, 59, 59)
        stmt = select(ForumLog).where(ForumLog.ts >= start, ForumLog.ts <= end)
        return list(self._db.scalars(stmt))
