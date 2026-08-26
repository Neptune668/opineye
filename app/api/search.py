"""主题检索路由：POST /api/search。"""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends

from app.api.deps import require_user
from app.dependencies import get_search_engine
from app.services.search_service import SearchEngine, SearchRequest

router = APIRouter(prefix="/api", tags=["search"])


class SearchBody(BaseModel):
    query: str = Field(..., description="主题词")
    source_types: list[str] = Field(default=["internal_data"], description="来源类型")


@router.post("/search")
def search(
    body: SearchBody,
    engine: SearchEngine = Depends(get_search_engine),
    _: object = Depends(require_user),
) -> dict:
    result = engine.search(SearchRequest(query=body.query, source_types=body.source_types))
    return {
        "code": 0,
        "message": "success",
        "data": {
            "task_id": result.task_id,
            "report": {
                "report_id": result.report.report_id,
                "topic": result.report.topic,
                "file_path": result.report.file_path,
            },
            "sources": [
                {
                    "source_type": s.source_type,
                    "title": s.title,
                    "url": s.url,
                    "summary": s.summary,
                    "published_at": s.published_at,
                }
                for s in result.sources
            ],
            "analysis": {
                "overview": result.analysis.overview,
                "timeline": [
                    {"ts": e.ts, "title": e.title} for e in result.analysis.timeline
                ],
                "channels": result.analysis.channels,
                "viewpoints": result.analysis.viewpoints,
                "sentiment": {
                    "positive": result.analysis.sentiment.positive,
                    "neutral": result.analysis.sentiment.neutral,
                    "negative": result.analysis.sentiment.negative,
                    "overall": result.analysis.sentiment.overall,
                },
                "risks": result.analysis.risks,
                "evidence": [
                    {"title": e.title, "url": e.url, "summary": e.summary, "ref": e.ref}
                    for e in result.analysis.evidence
                ],
            },
        },
    }
