"""洞察生成服务：基于分析结果生成洞察。"""
from __future__ import annotations

import logging
from typing import Any

from app.services.analysis_service import (
    SENTIMENT_NEGATIVE,
    SENTIMENT_POSITIVE,
)

logger = logging.getLogger(__name__)


def generate_insights(analysis: dict[str, Any]) -> list[str]:
    """基于情绪分布与观点生成洞察列表。"""
    insights: list[str] = []
    dist = analysis.get("sentiment_distribution", {})
    overall = analysis.get("overall_sentiment", "中性")
    viewpoints = analysis.get("viewpoints", [])

    insights.append(f"整体情绪倾向为「{overall}」。")

    if dist.get(SENTIMENT_NEGATIVE, 0) > 0:
        insights.append(
            f"存在 {dist[SENTIMENT_NEGATIVE]} 条负面情绪内容，建议关注风险点。"
        )
    if dist.get(SENTIMENT_POSITIVE, 0) > 0:
        insights.append(
            f"存在 {dist[SENTIMENT_POSITIVE]} 条正面情绪内容，传播态势良好。"
        )

    if viewpoints:
        sources = "、".join(v["source"] for v in viewpoints)
        insights.append(f"观点来源覆盖：{sources}。")

    if not viewpoints:
        insights.append("当前无可抽取的明确观点。")

    return insights
