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
from app.analysis.llm import LLMClient
from app.analysis.models import AnalysisOutput
from app.events.base import DomainEvent, EventBus, EventType
from app.exceptions import ValidationError
from app.services.collector import CollectRequest, Collector, SourceItem
from app.services.graph_builder import build_graph
from app.services.graph_service import FileGraphStore
from app.services.report_service import ReportMeta, ReportWriter
from app.utils.logging import get_logger
from app.utils.storage import GRAPHS_DIR

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
        llm_client: LLMClient | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._collector: Collector = collector
        self._report_writer: ReportWriter = report_writer
        self._graph_store: FileGraphStore = graph_store
        self._llm_client: LLMClient | None = llm_client
        self._event_bus: EventBus | None = event_bus

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
        # 尽力落库检索任务与来源（降级不阻断）
        self._persist_task(task_id, query, request.source_types, report.report_id, sources)
        # 发布 graph_ready 事件（G4）
        self._publish_graph_ready(report.report_id)
        # 发布 app_output 事件（G3 选项3：检索完成推分析摘要）
        self._publish_app_output("topic_search", analysis.overview)
        return SearchResult(task_id=task_id, sources=sources, analysis=analysis, report=report)

    def _publish_graph_ready(self, report_id: str) -> None:
        """发布 graph_ready 事件（含 report_id 与 graph 路径）。"""
        if self._event_bus is None:
            return
        graph_path = str(GRAPHS_DIR / report_id / "graph.json")
        self._event_bus.publish(
            DomainEvent(
                type=EventType.GRAPH_READY,
                payload={"report_id": report_id, "graph_path": graph_path},
            )
        )

    def _publish_app_output(self, app_name: str, output_text: str) -> None:
        """发布 app_output 事件（含 app_name 与 output_text）。"""
        if self._event_bus is None:
            return
        self._event_bus.publish(
            DomainEvent(
                type=EventType.APP_OUTPUT,
                payload={"app_name": app_name, "output_text": output_text},
            )
        )

    def _persist_task(
        self,
        task_id: str,
        query: str,
        source_types: list[str],
        report_id: str,
        sources: list[SourceItem],
    ) -> None:
        """尽力落库检索任务与来源记录，失败降级不阻断。"""
        try:
            from app.models.base import SessionLocal
            from app.models.search import SearchTask, Source

            db = SessionLocal()
            try:
                db.add(
                    SearchTask(
                        task_id=task_id,
                        query=query,
                        source_types=source_types,
                        status="completed",
                        report_id=report_id,
                    )
                )
                for s in sources:
                    db.add(
                        Source(
                            task_id=task_id,
                            source_type=s.source_type,
                            title=s.title,
                            url=s.url,
                            summary=s.summary,
                        )
                    )
                db.commit()
            finally:
                db.close()
        except Exception:  # noqa: BLE001 - 落库失败仅记录日志
            logger.exception("检索任务落库失败（降级）", extra={"task_id": task_id})

    def _analyze(self, query: str, sources: list[SourceItem]) -> AnalysisOutput:
        keywords = keyword.extract_keywords(sources)
        viewpoints = self._viewpoints(query, sources, keywords)
        risks = self._risks(sources)

        # 可选 LLM 增强：观点聚类与风险润色，失败自动回退规则结果
        if self._llm_client is not None and self._llm_client.available() and sources:
            viewpoints, risks = self._llm_enhance(query, sources, viewpoints, risks)

        return AnalysisOutput(
            overview=keyword.build_overview(query, sources, keywords),
            timeline=timeline.analyze(sources),
            channels=channel.analyze(sources),
            viewpoints=viewpoints,
            sentiment=sentiment.analyze(sources),
            risks=risks,
            evidence=evidence.analyze(sources, query),
        )

    def _llm_enhance(
        self,
        query: str,
        sources: list[SourceItem],
        viewpoints: list[str],
        risks: list[str],
    ) -> tuple[list[str], list[str]]:
        """用 LLM 增强观点与风险分析，失败回退规则结果。"""
        llm = self._llm_client
        if llm is None:
            return viewpoints, risks
        try:
            text = "；".join(f"{s.title}:{s.summary or ''}" for s in sources[:5])
            enhanced = llm.analyze(
                text, f"针对主题「{query}」总结核心观点与风险点，用换行分隔"
            )
            lines = [ln.strip("- ") for ln in enhanced.splitlines() if ln.strip()]
            if lines:
                return lines[:5], risks
        except Exception:  # noqa: BLE001
            logger.exception("LLM 增强失败，回退规则结果")
        return viewpoints, risks

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
