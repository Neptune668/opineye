"""重点证据提取：按来源相关性排序取 topN。"""

from __future__ import annotations

from app.analysis.models import EvidenceItem
from app.services.collector import SourceItem


def analyze(items: list[SourceItem], query: str, top_n: int = 10) -> list[EvidenceItem]:
    """按 query 在标题/摘要中的命中次数排序，取前 top_n 作为重点证据。"""
    scored: list[tuple[int, SourceItem]] = []
    q = query.strip().lower()
    for it in items:
        text = f"{it.title} {it.summary or ''}".lower()
        score = text.count(q) if q else 0
        scored.append((score, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    evidence = []
    for idx, (_, it) in enumerate(scored[:top_n]):
        evidence.append(
            EvidenceItem(
                title=it.title,
                url=it.url,
                summary=it.summary,
                ref=f"source#{idx}",
            )
        )
    return evidence
