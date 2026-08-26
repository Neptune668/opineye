"""情绪倾向判定（规则模式，精简情感词典）。

TODO(placeholder): 当前为精简词表，精度有限，见《未实现功能说明.md》2.6。
后续可替换为完整词典或 LLM 判定。
"""

from __future__ import annotations

from app.analysis.models import SentimentResult
from app.services.collector import SourceItem

# 精简情感词表（正向/负向）
POSITIVE_WORDS = {
    "好评", "满意", "支持", "赞", "优秀", "推荐", "期待", "正面", "积极",
    "增长", "突破", "创新", "受欢迎", "认可", "好评如潮", "利好", "看好",
    "改善", "提升", "成功", "领先", "优质", "火爆", "热销", "好评", "给力",
    "放心", "信赖", "惊喜", "喜欢", "满意",
}
NEGATIVE_WORDS = {
    "差评", "不满", "反对", "投诉", "质疑", "负面", "消极", "下降", "下滑",
    "亏损", "风险", "问题", "故障", "缺陷", "召回", "维权", "抵制", "失望",
    "恶化", "衰退", "失败", "落后", "劣质", "冷清", "滞销", "差劲", "担忧",
    "焦虑", "愤怒", "谴责", "批评", "隐患",
}


def analyze(items: list[SourceItem]) -> SentimentResult:
    """对来源列表做情绪倾向统计。"""
    pos = neu = neg = 0
    for it in items:
        text = f"{it.title} {it.summary or ''}"
        score = _score(text)
        if score > 0:
            pos += 1
        elif score < 0:
            neg += 1
        else:
            neu += 1

    if neg > pos and neg > neu:
        overall = "negative"
    elif pos > neg and pos > neu:
        overall = "positive"
    else:
        overall = "neutral"

    return SentimentResult(positive=pos, neutral=neu, negative=neg, overall=overall)


def _score(text: str) -> int:
    """命中正向词 +1、负向词 -1，加权求和。"""
    score = 0
    for w in POSITIVE_WORDS:
        if w in text:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in text:
            score -= 1
    return score
