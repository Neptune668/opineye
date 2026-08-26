"""图谱模块：GraphStore 接口、图谱构建与文件存储。

职责：图谱结果加载、指定报告查询、关系检索。
节点最小字段：节点标识、节点类型、关系类型、来源引用（需求 2.2.8）。
文件布局：graphs/{report_id}/graph.json。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.analysis.models import AnalysisOutput
from app.utils.logging import get_logger
from app.utils.storage import GRAPHS_DIR, read_json, write_json

logger = get_logger(__name__)


@dataclass(frozen=True)
class GraphNode:
    """图谱节点。"""

    node_id: str
    node_type: str
    label: str
    ref: str | None = None


@dataclass(frozen=True)
class GraphEdge:
    """图谱边。"""

    source: str
    target: str
    relation_type: str
    ref: str | None = None


@dataclass(frozen=True)
class GraphData:
    """图谱数据。"""

    report_id: str = ""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


class GraphStore(Protocol):
    """图谱存储接口（契约，冻结）。"""

    def load(self, report_id: str) -> GraphData: ...

    def latest(self) -> GraphData: ...

    def query(self, report_id: str, cond: dict) -> GraphData: ...


class FileGraphStore:
    """基于文件的图谱存储实现。"""

    def __init__(self, graphs_dir: Path = GRAPHS_DIR) -> None:
        self._graphs_dir = graphs_dir

    def save(self, graph: GraphData) -> None:
        """保存图谱到 graphs/{report_id}/graph.json。"""
        path = self._graphs_dir / graph.report_id / "graph.json"
        write_json(
            path,
            {
                "report_id": graph.report_id,
                "nodes": [n.__dict__ for n in graph.nodes],
                "edges": [e.__dict__ for e in graph.edges],
            },
        )
        logger.info("图谱已保存", extra={"report_id": graph.report_id})

    def load(self, report_id: str) -> GraphData:
        path = self._graphs_dir / report_id / "graph.json"
        raw = read_json(path, default=None)
        if raw is None:
            return GraphData(report_id=report_id)
        return self._from_dict(raw)

    def latest(self) -> GraphData:
        """返回最新一份图谱（按目录修改时间）。"""
        report_dirs = [d for d in self._graphs_dir.iterdir() if d.is_dir()] if self._graphs_dir.exists() else []
        if not report_dirs:
            return GraphData()
        latest_dir = max(report_dirs, key=lambda d: d.stat().st_mtime)
        return self.load(latest_dir.name)

    def query(self, report_id: str, cond: dict) -> GraphData:
        """按节点/关系条件查询图谱。"""
        graph = self.load(report_id)
        node_id = cond.get("node_id")
        relation_type = cond.get("relation_type")

        nodes = graph.nodes
        edges = graph.edges

        if node_id:
            # 过滤与该节点相关的边，并保留关联节点
            related = {node_id}
            matched_edges = [
                e for e in edges if e.source == node_id or e.target == node_id
            ]
            for e in matched_edges:
                related.add(e.source)
                related.add(e.target)
            nodes = [n for n in nodes if n.node_id in related]
            edges = matched_edges

        if relation_type:
            edges = [e for e in edges if e.relation_type == relation_type]

        return GraphData(report_id=report_id, nodes=nodes, edges=edges)

    @staticmethod
    def _from_dict(raw: dict) -> GraphData:
        return GraphData(
            report_id=raw.get("report_id", ""),
            nodes=[GraphNode(**n) for n in raw.get("nodes", [])],
            edges=[GraphEdge(**e) for e in raw.get("edges", [])],
        )
