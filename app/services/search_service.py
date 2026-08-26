"""检索分析模块：SearchEngine 接口与规则模式实现。

职责：调用 Collector 采集，再经分析子引擎产出结构化分析结果。
不负责报告文件写入（T8）与图谱构建（T10）。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Protocol

from app.analysis import channel, evidence, keyword, sentiment, timeline
from app.analysis.models import AnalysisOutput
from app.exceptions import ValidationError
from app.services.collector import CollectRequest, Collector, SourceItem
from app.services.graph_builder import build_graph
from app.services.graph_service import FileGraphStore
from app.services.report_service import ReportMeta, ReportWriter
from app.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class SearchRequest:
    query: str
    source_types: list[str]


@dataclass(frozen=True)
class SearchResult:
    task_id: str
    sources: list[SourceItem]
    analysis: AnalysisOutput
    report: ReportMeta


class SearchEngine(Protocol):
    """检索分析引擎接口（契约，冻结）。"""

    def search(self, request: SearchRequest) -> SearchResult: ...


class RuleSearchEngine:
    """基于规则的分析引擎实现。

    检索流程内同步生成报告（方案 A）。
    """

    def __init__(
        self,
        collector: Collector,
        report_writer: ReportWriter,
        graph_store: FileGraphStore,
    ) -> None:
        self._collector: Collector = collector
        self._report_writer: ReportWriter = report_writer
        self._graph_store: FileGraphStore = graph_store

    def search(self, request: SearchRequest) -> SearchResult:
        query = request.query.strip()
        if not query:
            raise ValidationError("query 不能为空")

        task_id = f"tsk_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        sources = self._collector.collect(
            CollectRequest(query=query, source_types=request.source_types)
        )
        analysis = self._analyze(query, sources)
        # 方案 A：检索内同步生成报告
        report = self._report_writer.write(analysis, query)
        # 同步生成图谱
        graph = build_graph(report.report_id, query, analysis)
        self._graph_store.save(graph)
        return SearchResult(task_id=task_id, sources=sources, analysis=analysis, report=report)

    def _analyze(self, query: str, sources: list[SourceItem]) -> AnalysisOutput:
        keywords = keyword.extract_keywords(sources)
        return AnalysisOutput(
            overview=keyword.build_overview(query, sources, keywords),
            timeline=timeline.analyze(sources),
            channels=channel.analyze(sources),
            viewpoints=self._viewpoints(query, sources, keywords),
            sentiment=sentiment.analyze(sources),
            risks=self._risks(sources),
            evidence=evidence.analyze(sources, query),
        )

    @staticmethod
    def _viewpoints(query: str, sources: list[SourceItem], keywords: list[str]) -> list[str]:
        """规则模式观点抽取：基于关键词生成观点条目。"""
        if not sources:
            return []
        top_kw = keywords[:3] if keywords else [query]
        viewpoints = [f"围绕「{kw}」的相关讨论较为集中" for kw in top_kw]
        viewpoints.append(f"共 {len(sources)} 条来源参与讨论，覆盖多类传播渠道")
        return viewpoints

    @staticmethod
    def _risks(sources: list[SourceItem]) -> list[str]:
        """规则模式风险判断：结合情绪倾向给出提示。"""
        senti = sentiment.analyze(sources)
        risks: list[str] = []
        if senti.negative > senti.positive:
            risks.append("负面情绪占比偏高，需关注舆论走向")
        if not sources:
            risks.append("数据量不足，存在信息盲区风险")
        if not risks:
            risks.append("当前未发现显著高风险点")
        return risks
