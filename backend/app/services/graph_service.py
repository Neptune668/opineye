"""图谱服务：图谱生成、加载、按报告查询、关系检索。"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app import settings
from app.core import store

logger = logging.getLogger(__name__)

# 节点类型
NODE_TYPES = ("topic", "person", "org", "event", "source", "keyword")
# 关系类型
EDGE_TYPES = ("mentions", "related_to", "published_by", "sourced_from")

# 来源类型 → 节点类型映射
_SOURCE_NODE_TYPE = {
    "news": "source",
    "image": "source",
    "video": "source",
    "forum_post": "event",
    "internal_data": "source",
}


def generate_graph(report_id: str, record: dict[str, Any]) -> dict[str, Any]:
    """根据检索记录生成图谱数据。"""
    topic = record.get("topic", "")
    items = record.get("items", [])

    nodes: list[dict[str, Any]] = [
        {
            "id": "n0",
            "label": topic,
            "type": "topic",
            "source_ref": f"search:{report_id}",
        }
    ]

    # 每个来源条目生成一个节点，并与主题节点建立 sourced_from 关系
    for i, item in enumerate(items, start=1):
        node_id = f"n{i}"
        st = item.get("source_type", "source")
        nodes.append(
            {
                "id": node_id,
                "label": item.get("title", st),
                "type": _SOURCE_NODE_TYPE.get(st, "source"),
                "source_ref": f"{st}:{item.get('title', '')}",
            }
        )

    edges: list[dict[str, Any]] = []
    for i in range(1, len(nodes)):
        edges.append(
            {
                "id": f"e{i}",
                "source": "n0",
                "target": f"n{i}",
                "type": "sourced_from",
                "source_ref": f"search:{report_id}",
            }
        )

    graph = {
        "report_id": report_id,
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "topic": topic,
        },
        "nodes": nodes,
        "edges": edges,
    }
    return graph


def save_graph(report_id: str, graph: dict[str, Any]) -> str:
    """保存图谱到 graphs/{report_id}/graph.json，返回路径。"""
    graph_dir = settings.GRAPHS_DIR / report_id
    graph_dir.mkdir(parents=True, exist_ok=True)
    path = graph_dir / "graph.json"
    store.write_json(path, graph)
    logger.info("图谱已生成：%s", path)
    return str(path)


def load_graph(report_id: str) -> dict[str, Any] | None:
    """加载指定报告图谱。"""
    path = settings.GRAPHS_DIR / report_id / "graph.json"
    if not path.exists():
        return None
    return store.read_json(path)


def latest_graph() -> dict[str, Any] | None:
    """加载最新图谱（按目录修改时间倒序）。"""
    graphs_dir = settings.GRAPHS_DIR
    if not graphs_dir.exists():
        return None
    dirs = [d for d in graphs_dir.iterdir() if d.is_dir()]
    if not dirs:
        return None
    latest = max(dirs, key=lambda d: d.stat().st_mtime)
    graph = load_graph(latest.name)
    if graph:
        graph["report_id"] = latest.name
    return graph


def query_graph(
    graph: dict[str, Any],
    node: str | None = None,
    relation: str | None = None,
) -> dict[str, Any]:
    """按节点或关系条件过滤图谱，返回 nodes/edges。"""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if node:
        node_ids = {n["id"] for n in nodes if node in n.get("label", "") or node == n["id"]}
        nodes = [n for n in nodes if n["id"] in node_ids]
        edges = [
            e for e in edges
            if e["source"] in node_ids or e["target"] in node_ids
        ]

    if relation:
        edges = [e for e in edges if e.get("type") == relation]

    return {"nodes": nodes, "edges": edges}


def list_report_ids() -> list[str]:
    """列出全部已有报告编号（按时间倒序）。"""
    graphs_dir = settings.GRAPHS_DIR
    if not graphs_dir.exists():
        return []
    dirs = [d for d in graphs_dir.iterdir() if d.is_dir()]
    dirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
    return [d.name for d in dirs]
