"""图谱模块路由：/api/graph/latest、/api/graph/{report_id}、/api/graph/query。

权限：允许 viewer 及以上。
"""

from __future__ import annotations

from pydantic import BaseModel

from fastapi import APIRouter, Depends

from app.api.deps import require_viewer
from app.dependencies import get_graph_store
from app.services.graph_service import FileGraphStore, GraphData

router = APIRouter(prefix="/api/graph", tags=["graph"])


class QueryBody(BaseModel):
    report_id: str
    node_id: str | None = None
    relation_type: str | None = None


def _serialize(g: GraphData) -> dict:
    return {
        "report_id": g.report_id,
        "nodes": [
            {"node_id": n.node_id, "node_type": n.node_type, "label": n.label, "ref": n.ref}
            for n in g.nodes
        ],
        "edges": [
            {"source": e.source, "target": e.target, "relation_type": e.relation_type, "ref": e.ref}
            for e in g.edges
        ],
    }


@router.get("/latest")
def latest(
    store: FileGraphStore = Depends(get_graph_store),
    _: object = Depends(require_viewer),
) -> dict:
    return {"code": 0, "message": "success", "data": _serialize(store.latest())}


@router.get("/{report_id}")
def get_graph(
    report_id: str,
    store: FileGraphStore = Depends(get_graph_store),
    _: object = Depends(require_viewer),
) -> dict:
    return {"code": 0, "message": "success", "data": _serialize(store.load(report_id))}


@router.post("/query")
def query(
    body: QueryBody,
    store: FileGraphStore = Depends(get_graph_store),
    _: object = Depends(require_viewer),
) -> dict:
    cond = {}
    if body.node_id:
        cond["node_id"] = body.node_id
    if body.relation_type:
        cond["relation_type"] = body.relation_type
    return {"code": 0, "message": "success", "data": _serialize(store.query(body.report_id, cond))}
