"""关键词抽取与事件概述（规则模式，jieba 中文分词）。

中文使用 jieba 分词，英文保留整词；结合停用词过滤与词频统计抽取关键词，
并将查询词强制纳入关键词，保证报告/图谱的关键词为有意义的词组。
"""

from __future__ import annotations

import logging
from collections import Counter

import jieba

from app.services.collector import SourceItem

# 静默 jieba 首次加载词典时的 stderr 提示
jieba.setLogLevel(logging.ERROR)

# 停用词（精简，可按需扩充）
_STOPWORDS = {
    "的", "了", "和", "与", "或", "是", "在", "对", "及", "等", "中", "为",
    "关于", "一个", "以及", "进行", "我们", "你们", "他们", "这个", "那个",
    "这", "那", "有", "被", "从", "到", "并", "而", "但", "也", "都", "就",
    "会", "能", "要", "可", "已经", "正在", "通过", "针对", "相关", "表示",
    "认为", "目前", "其中", "同时", "以及", "并且", "或者",
}

# 无信息量的纯标点/空白/数字
def _is_noise(token: str) -> bool:
    return not any(ch.isalnum() or "一" <= ch <= "鿿" for ch in token)


def extract_keywords(items: list[SourceItem], query: str = "", top_n: int = 10) -> list[str]:
    """基于 jieba 分词 + 词频统计抽取关键词，查询词优先置顶。"""
    counter: Counter[str] = Counter()
    for it in items:
        for w in _tokenize(f"{it.title} {it.summary or ''}"):
            if len(w) >= 2 and w not in _STOPWORDS and not _is_noise(w):
                counter[w] += 1

    keywords = [w for w, _ in counter.most_common(top_n)]

    # 查询词（或其分词结果）强制纳入，保证与主题强相关
    for qw in _tokenize(query):
        if len(qw) >= 2 and qw not in _STOPWORDS and qw not in keywords:
            keywords.insert(0, qw)
    return keywords[:top_n]


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
    """jieba 分词：中文按词切分，英文按空格切分为整词。"""
    tokens: list[str] = []
    for part in jieba.cut(text):
        part = part.strip()
        if not part:
            continue
        # 纯英文/数字片段按空格再切一次，保证整词
        if part.isascii():
            tokens.extend(p for p in part.split() if p)
        else:
            tokens.append(part)
    return tokens
