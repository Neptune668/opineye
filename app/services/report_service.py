"""报告生成模块：ReportWriter 接口与实现。

职责：将 SearchResult 渲染为 8 节结构化 Markdown 报告并写入文件，
同时尽力落库报告元数据（失败降级不阻断）。
对应需求 2.2.11 报告输出格式。
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.analysis.models import AnalysisOutput
from app.utils.logging import get_logger
from app.utils.storage import REPORTS_DIR

logger = get_logger(__name__)


@dataclass(frozen=True)
class ReportMeta:
    """报告元数据。"""

    report_id: str
    topic: str
    file_path: str


class ReportWriter(Protocol):
    """报告生成接口（契约，冻结）。"""

    def write(self, analysis: AnalysisOutput, topic: str) -> ReportMeta: ...


class MarkdownReportWriter:
    """将分析结果渲染为 Markdown 报告并落盘。

    落库为「尽力而为」：report_repository 为 None 或落库异常时，仅记录日志，
    不影响报告文件产物（对应文档 8.5 降级策略）。
    """

    def __init__(
        self,
        reports_dir: Path = REPORTS_DIR,
        report_repository=None,
    ) -> None:
        self._reports_dir = reports_dir
        self._report_repository = report_repository

    def write(self, analysis: AnalysisOutput, topic: str) -> ReportMeta:
        report_id = f"rpt_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        content = self._render(analysis, topic)
        path = self._reports_dir / report_id / "report.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        meta = ReportMeta(report_id=report_id, topic=topic, file_path=str(path))
        self._persist(meta)
        logger.info("报告已生成", extra={"report_id": report_id, "topic": topic})
        return meta

    def _persist(self, meta: ReportMeta) -> None:
        """尽力落库报告元数据，失败降级不阻断。

        每次创建独立 session，避免单例绑定 session 导致生命周期混乱。
        """
        try:
            from app.models.base import SessionLocal
            from app.models.report import Report

            db = SessionLocal()
            try:
                db.add(Report(report_id=meta.report_id, topic=meta.topic, file_path=meta.file_path))
                db.commit()
            finally:
                db.close()
        except Exception:  # noqa: BLE001 - 落库失败仅记录日志
            logger.exception("报告元数据落库失败（降级）", extra={"report_id": meta.report_id})

    # ---- 渲染 ----

    def _render(self, a: AnalysisOutput, topic: str) -> str:
        lines: list[str] = []
        lines.append(f"# 舆情分析报告：{topic}")
        lines.append("")
        lines.append("## 事件概述")
        lines.append(a.overview)
        lines.append("")
        lines.append("## 时间线")
        if a.timeline:
            for e in a.timeline:
                ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(e.ts))
                lines.append(f"- {ts} - {e.title}")
        else:
            lines.append("- （无时间线数据）")
        lines.append("")
        lines.append("## 传播渠道")
        if a.channels:
            for ch, cnt in a.channels.items():
                lines.append(f"- {ch}: {cnt}")
        else:
            lines.append("- （无传播渠道数据）")
        lines.append("")
        lines.append("## 主要观点")
        if a.viewpoints:
            for v in a.viewpoints:
                lines.append(f"- {v}")
        else:
            lines.append("- （无观点数据）")
        lines.append("")
        lines.append("## 情绪倾向")
        lines.append(
            f"- 正向：{a.sentiment.positive}，中性：{a.sentiment.neutral}，"
            f"负向：{a.sentiment.negative}，整体：{a.sentiment.overall}"
        )
        lines.append("")
        lines.append("## 风险判断")
        if a.risks:
            for r in a.risks:
                lines.append(f"- {r}")
        else:
            lines.append("- （无风险数据）")
        lines.append("")
        lines.append("## 重点证据")
        if a.evidence:
            for ev in a.evidence:
                lines.append(f"- **{ev.title}**")
                if ev.url:
                    lines.append(f"  - 链接：{ev.url}")
                if ev.summary:
                    lines.append(f"  - 摘要：{ev.summary}")
                if ev.ref:
                    lines.append(f"  - 引用：{ev.ref}")
        else:
            lines.append("- （无证据数据）")
        lines.append("")
        lines.append("## 结论摘要")
        lines.append(self._conclusion(a, topic))
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _conclusion(a: AnalysisOutput, topic: str) -> str:
        overall = a.sentiment.overall
        if not a.evidence and not a.timeline:
            return f"针对主题「{topic}」暂未获得充分数据，建议扩大采集范围或补充数据源后重新分析。"
        return (
            f"综合来看，主题「{topic}」的整体情绪倾向为「{overall}」，"
            f"共采集 {len(a.evidence)} 条重点证据。建议持续关注相关风险点，并结合时间线走势制定应对策略。"
        )
