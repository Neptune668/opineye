"""报告汇总服务：拼装 8 段式 report.md。"""
from __future__ import annotations

import logging
from typing import Any

from app import settings
from app.core import store
from app.services.analysis_service import (
    SENTIMENT_NEGATIVE,
    SENTIMENT_NEUTRAL,
    SENTIMENT_POSITIVE,
)
from app.services.insight_service import generate_insights

logger = logging.getLogger(__name__)

# 8 段标题（顺序固定）
_SECTIONS = [
    "事件概述",
    "时间线",
    "传播渠道",
    "主要观点",
    "情绪倾向",
    "风险判断",
    "重点证据",
    "结论摘要",
]


def build_report(
    report_id: str, record: dict[str, Any], analysis: dict[str, Any]
) -> str:
    """拼装 8 段式 Markdown 报告。"""
    topic = record.get("topic", "")
    items = record.get("items", [])
    insights = generate_insights(analysis)

    lines: list[str] = []
    lines.append(f"# 舆情分析报告：{topic}")
    lines.append("")
    lines.append(f"> 报告编号：{report_id}")
    lines.append(f"> 执行时间：{record.get('executed_at', '')}")
    lines.append("")

    # 1. 事件概述
    lines.append("## 一、事件概述")
    lines.append("")
    lines.append(f"本报告针对主题「{topic}」进行舆情分析，覆盖来源类型："
                 f"{'、'.join(record.get('source_types', []))}，"
                 f"共采集来源条目 {len(items)} 条。")
    lines.append("")

    # 2. 时间线
    lines.append("## 二、时间线")
    lines.append("")
    sorted_items = sorted(items, key=lambda x: x.get("collected_at", ""))
    for it in sorted_items:
        lines.append(f"- {it.get('collected_at', '')}　{it.get('source_type', '')}："
                     f"{it.get('title', '')}")
    lines.append("")

    # 3. 传播渠道
    lines.append("## 三、传播渠道")
    lines.append("")
    for s in record.get("source_summary", []):
        lines.append(f"- {s['source_type']}：{s['count']} 条")
    lines.append("")

    # 4. 主要观点
    lines.append("## 四、主要观点")
    lines.append("")
    for v in analysis.get("viewpoints", []):
        lines.append(f"- 【{v['source']}】{v['summary']}（{v['count']} 条）")
    lines.append("")

    # 5. 情绪倾向
    lines.append("## 五、情绪倾向")
    lines.append("")
    dist = analysis.get("sentiment_distribution", {})
    lines.append(f"- 整体判断：**{analysis.get('overall_sentiment', '中性')}**")
    lines.append(f"- 正向：{dist.get(SENTIMENT_POSITIVE, 0)} 条")
    lines.append(f"- 中性：{dist.get(SENTIMENT_NEUTRAL, 0)} 条")
    lines.append(f"- 负向：{dist.get(SENTIMENT_NEGATIVE, 0)} 条")
    lines.append("")

    # 6. 风险判断
    lines.append("## 六、风险判断")
    lines.append("")
    if dist.get(SENTIMENT_NEGATIVE, 0) > 0:
        lines.append(f"- 高风险点：存在 {dist[SENTIMENT_NEGATIVE]} 条负面情绪内容，需重点关注。")
    else:
        lines.append("- 高风险点：暂未发现明显负面聚集。")
    lines.append("- 关注事项：持续监控情绪变化与传播扩散。")
    lines.append("")

    # 7. 重点证据
    lines.append("## 七、重点证据")
    lines.append("")
    for it in items:
        lines.append(f"- 标题：{it.get('title', '')}")
        lines.append(f"  - 链接：{it.get('url', '')}")
        lines.append(f"  - 摘要：{it.get('text', '')}")
        lines.append(f"  - 来源引用：{it.get('source_type', '')}")
    lines.append("")

    # 8. 结论摘要
    lines.append("## 八、结论摘要")
    lines.append("")
    for ins in insights:
        lines.append(f"- {ins}")
    lines.append("")

    return "\n".join(lines)


def save_report(report_id: str, report_md: str) -> str:
    """将报告写入 reports/{report_id}/report.md，返回路径。"""
    report_dir = settings.REPORTS_DIR / report_id
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / "report.md"
    store.write_text(path, report_md)
    logger.info("报告已生成：%s", path)
    return str(path)


def generate_report(record: dict[str, Any], analysis: dict[str, Any]) -> tuple[str, str]:
    """一步生成报告：拼装 + 落盘，返回 (report_id, report_md)。"""
    report_id = record["report_id"]
    report_md = build_report(report_id, record, analysis)
    save_report(report_id, report_md)
    return report_id, report_md
