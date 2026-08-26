"""图谱接口：最新/指定图谱查询、节点/关系查询。"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import ApiResponse, GraphQueryRequest
from app.services import graph_service

router = APIRouter(tags=["graph"])


@router.get("/api/graph/latest")
async def graph_latest():
    graph = graph_service.latest_graph()
    if graph is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    return ApiResponse(data={"report_id": graph.get("report_id"), "graph": graph})


@router.get("/api/graph/{report_id}")
async def graph_by_id(report_id: str):
    graph = graph_service.load_graph(report_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    return ApiResponse(data={"report_id": report_id, "graph": graph})


@router.post("/api/graph/query")
async def graph_query(req: GraphQueryRequest):
    report_id = req.report_id
    graph = graph_service.load_graph(report_id) if report_id else graph_service.latest_graph()
    if graph is None:
        raise HTTPException(status_code=404, detail="资源不存在")
    result = graph_service.query_graph(graph, node=req.node, relation=req.relation)
    return ApiResponse(data=result)
