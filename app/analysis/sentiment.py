"""情绪倾向判定（规则模式，扩充情感词典）。

内置扩充后的情感词表（正向/负向），并支持从外部词典文件加载更多词。
见《未实现功能说明.md》2.6 的局限与增强说明。
"""

from __future__ import annotations

from pathlib import Path

from app.analysis.models import SentimentResult
from app.services.collector import SourceItem

# 扩充情感词表（正向）
POSITIVE_WORDS = {
    # 基础正向
    "好评", "满意", "支持", "赞", "优秀", "推荐", "期待", "正面", "积极",
    "增长", "突破", "创新", "受欢迎", "认可", "好评如潮", "利好", "看好",
    "改善", "提升", "成功", "领先", "优质", "火爆", "热销", "给力",
    "放心", "信赖", "惊喜", "喜欢", "满意", "点赞", "称赞", "赞美",
    # 扩展正向
    "出色", "卓越", "一流", "顶尖", "精品", "亮眼", "惊艳", "给力",
    "叫好", "追捧", "抢购", "供不应求", "口碑", "赞誉", "信赖", "靠谱",
    "稳健", "强劲", "繁荣", "回暖", "向好", "攀升", "创纪录", "新高",
    "突破性", "里程碑", "领跑", "夺冠", "优胜", "卓越", "好评如潮",
    "物超所值", "性价比", "值得", "推荐", "放心购", "无忧", "贴心",
    "高效", "稳定", "可靠", "耐用", "实用", "便捷", "舒适", "美观",
    "时尚", "高端", "大气", "精致", "专业", "权威", "口碑爆棚",
}

# 扩充情感词表（负向）
NEGATIVE_WORDS = {
    # 基础负向
    "差评", "不满", "反对", "投诉", "质疑", "负面", "消极", "下降", "下滑",
    "亏损", "风险", "问题", "故障", "缺陷", "召回", "维权", "抵制", "失望",
    "恶化", "衰退", "失败", "落后", "劣质", "冷清", "滞销", "差劲", "担忧",
    "焦虑", "愤怒", "谴责", "批评", "隐患", "投诉", "吐槽", "失望",
    # 扩展负向
    "糟糕", "糟糕透顶", "坑", "坑爹", "骗局", "虚假", "夸大", "缩水",
    "翻车", "崩盘", "暴跌", "腰斩", "重挫", "亏损", "危机", "丑闻",
    "造假", "山寨", "劣质", "低劣", "粗糙", "敷衍", "欺骗", "误导",
    "涨价", "缺货", "断货", "翻新", "二手", "问题频出", "故障率",
    "卡顿", "死机", "发热", "续航差", "信号差", "售后差", "态度差",
    "霸王条款", "套路", "割韭菜", "跑路", "倒闭", "裁员", "停摆",
    "抵制", "拒买", "差劲", "难用", "鸡肋", "失望", "寒心", "心寒",
    "愤怒", "不满", "抗议", "声讨", "曝光", "揭秘", "内幕",
}

# 可选外部词典文件（data/sentiment_words.txt，每行一个词，前缀 + 或 - 表示极性）
_EXTERNAL_DICT = Path(__file__).resolve().parent.parent.parent / "data" / "sentiment_words.txt"


def _load_external_words() -> tuple[set[str], set[str]]:
    """加载外部情感词典（若存在），扩充内置词表。"""
    pos: set[str] = set()
    neg: set[str] = set()
    if not _EXTERNAL_DICT.exists():
        return pos, neg
    try:
        for line in _EXTERNAL_DICT.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("+"):
                pos.add(line[1:].strip())
            elif line.startswith("-"):
                neg.add(line[1:].strip())
    except OSError:
        pass
    return pos, neg


_EXT_POS, _EXT_NEG = _load_external_words()
ALL_POSITIVE = POSITIVE_WORDS | _EXT_POS
ALL_NEGATIVE = NEGATIVE_WORDS | _EXT_NEG


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
    for w in ALL_POSITIVE:
        if w in text:
            score += 1
    for w in ALL_NEGATIVE:
        if w in text:
            score -= 1
    return score
