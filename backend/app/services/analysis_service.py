"""内容分析服务：观点抽取 + 情绪三分类。

情绪判定当前采用 rule_based（规则词典），预留 llm 模式接口。
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# 情绪倾向枚举
SENTIMENT_POSITIVE = "正向"
SENTIMENT_NEUTRAL = "中性"
SENTIMENT_NEGATIVE = "负向"

# 规则词典（可扩展）
_POSITIVE_WORDS = {
    "好评", "满意", "支持", "点赞", "认可", "好评如潮", "正面", "推荐",
    "优秀", "给力", "赞", "喜欢", "放心", "信赖", "靠谱", "突破", "利好",
}
_NEGATIVE_WORDS = {
    "差评", "不满", "反对", "抵制", "投诉", "负面", "批评", "质疑",
    "糟糕", "失望", "愤怒", "担忧", "风险", "隐患", "曝光", "造假",
    "欺骗", "抵制", "翻车", "暴跌", "危机",
}


def classify_sentiment(text: str) -> str:
    """基于规则词典判定情绪倾向。"""
    pos_count = sum(1 for w in _POSITIVE_WORDS if w in text)
    neg_count = sum(1 for w in _NEGATIVE_WORDS if w in text)

    if pos_count > neg_count:
        return SENTIMENT_POSITIVE
    if neg_count > pos_count:
        return SENTIMENT_NEGATIVE
    return SENTIMENT_NEUTRAL


def extract_viewpoints(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """从来源条目中抽取观点（按来源角色聚合）。

    每个条目至少含 source_type（来源类型）与 text（文本）。
    """
    viewpoints: dict[str, list[str]] = {}
    for item in items:
        source = item.get("source_type", "unknown")
        text = item.get("text", "")
        if not text:
            continue
        viewpoints.setdefault(source, []).append(text)
    return [
        {"source": source, "summary": _summarize(texts), "count": len(texts)}
        for source, texts in viewpoints.items()
    ]


def _summarize(texts: list[str]) -> str:
    """简单摘要：取首条文本截断。"""
    if not texts:
        return ""
    head = texts[0].strip()
    return head if len(head) <= 60 else head[:60] + "…"


def analyze(items: list[dict[str, Any]]) -> dict[str, Any]:
    """综合分析：返回情绪分布与观点列表。"""
    sentiments = [classify_sentiment(item.get("text", "")) for item in items]
    dist = {
        SENTIMENT_POSITIVE: sentiments.count(SENTIMENT_POSITIVE),
        SENTIMENT_NEUTRAL: sentiments.count(SENTIMENT_NEUTRAL),
        SENTIMENT_NEGATIVE: sentiments.count(SENTIMENT_NEGATIVE),
    }
    overall = _overall_sentiment(dist)
    viewpoints = extract_viewpoints(items)
    return {
        "sentiment_distribution": dist,
        "overall_sentiment": overall,
        "viewpoints": viewpoints,
    }


def _overall_sentiment(dist: dict[str, int]) -> str:
    """按数量占比给出整体判断（无数据时中性）。"""
    total = sum(dist.values())
    if total == 0:
        return SENTIMENT_NEUTRAL
    if dist[SENTIMENT_POSITIVE] > dist[SENTIMENT_NEGATIVE]:
        return SENTIMENT_POSITIVE
    if dist[SENTIMENT_NEGATIVE] > dist[SENTIMENT_POSITIVE]:
        return SENTIMENT_NEGATIVE
    return SENTIMENT_NEUTRAL
