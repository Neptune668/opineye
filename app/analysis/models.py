"""分析结果数据模型（契约，冻结）。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TimelineEvent:
    """时间线事件。"""

    ts: float
    title: str


@dataclass(frozen=True)
class SentimentResult:
    """情绪倾向统计结果。"""

    positive: int = 0
    neutral: int = 0
    negative: int = 0
    overall: str = "neutral"  # positive / neutral / negative


@dataclass(frozen=True)
class EvidenceItem:
    """重点证据条目。"""

    title: str
    url: str | None = None
    summary: str | None = None
    ref: str = ""  # 引用位置（来源索引/ID）


@dataclass(frozen=True)
class AnalysisOutput:
    """结构化分析结果（对应需求 2.2.11 报告 8 节，结论摘要由 T8 汇总）。"""

    overview: str = ""                          # 事件概述
    timeline: list[TimelineEvent] = field(default_factory=list)
    channels: dict[str, int] = field(default_factory=dict)   # 传播渠道分布
    viewpoints: list[str] = field(default_factory=list)      # 主要观点
    sentiment: SentimentResult = field(default_factory=SentimentResult)
    risks: list[str] = field(default_factory=list)           # 风险判断
    evidence: list[EvidenceItem] = field(default_factory=list)  # 重点证据
