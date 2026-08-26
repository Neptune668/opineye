"""主题检索接口：POST /api/search。"""
from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ApiResponse, SearchRequest, SearchResult
from app.services import analysis_service, graph_service, report_service, search_service

router = APIRouter(tags=["search"])


@router.post("/api/search")
async def search(req: SearchRequest):
    """主题检索 + 分析 + 报告 + 图谱一站式流程。"""
    # 1. 检索
    record = await search_service.search(req.query, req.source_types)
    # 2. 内容分析
    analysis = analysis_service.analyze(record["items"])
    # 3. 报告生成
    report_id, report_md = report_service.generate_report(record, analysis)
    # 4. 图谱生成
    graph = graph_service.generate_graph(report_id, record)
    graph_path = graph_service.save_graph(report_id, graph)

    # 5. 广播图谱生成完成
    try:
        from app.core.ws_manager import ws_manager
        await ws_manager.broadcast(
            {
                "type": "graph_ready",
                "data": {"report_id": report_id, "graph_path": graph_path},
            }
        )
    except Exception:
        pass

    return ApiResponse(
        data=SearchResult(
            report_id=report_id,
            report_md=report_md,
            graph_path=graph_path,
        )
    )
