"""关键词抽取与事件概述（规则模式）。"""

from __future__ import annotations

import re
from collections import Counter

from app.services.collector import SourceItem

# 停用词（精简）
_STOPWORDS = {
    "的", "了", "和", "与", "或", "是", "在", "对", "及", "等", "中", "为",
    "关于", "一个", "以及", "进行", "我们", "你们", "他们", "这个", "那个",
}


def extract_keywords(items: list[SourceItem], top_n: int = 10) -> list[str]:
    """基于标题/摘要词频统计抽取关键词。"""
    counter: Counter[str] = Counter()
    for it in items:
        words = _tokenize(f"{it.title} {it.summary or ''}")
        for w in words:
            if len(w) >= 2 and w not in _STOPWORDS:
                counter[w] += 1
    return [w for w, _ in counter.most_common(top_n)]


def build_overview(query: str, items: list[SourceItem], keywords: list[str]) -> str:
    """生成事件概述文本。"""
    if not items:
        return f"针对主题「{query}」未采集到相关数据，无法形成有效分析。"
    kw = "、".join(keywords[:5]) if keywords else query
    return (
        f"本报告围绕主题「{query}」展开，共采集到 {len(items)} 条相关信息，"
        f"涉及关键词：{kw}。以下从时间线、传播渠道、主要观点、情绪倾向等维度进行分析。"
    )


def _tokenize(text: str) -> list[str]:
    """中文按字符切分，英文按空格切分（简化分词）。"""
    text = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    tokens: list[str] = []
    for part in text.split():
        if re.fullmatch(r"[\u4e00-\u9fff]+", part):
            # 中文逐字（简化，实际应使用分词库）
            tokens.extend(list(part))
        else:
            tokens.append(part.lower())
    return tokens
