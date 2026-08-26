"""报告生成应用（单功能应用子进程入口）。

启动后读取最新一次检索记录，重新生成 8 段式报告。
"""
from __future__ import annotations

import asyncio
import sys

from app import settings
from app.core import store
from app.services import analysis_service, report_service


def _load_latest_record() -> dict | None:
    """读取最新一次检索记录（reports/{report_id}/sources.json）。"""
    reports_dir = settings.REPORTS_DIR
    if not reports_dir.exists():
        return None
    dirs = [d for d in reports_dir.iterdir() if d.is_dir()]
    if not dirs:
        return None
    latest = max(dirs, key=lambda d: d.stat().st_mtime)
    path = latest / "sources.json"
    if not path.exists():
        return None
    return store.read_json(path)


async def main() -> None:
    print("[report] 报告生成应用已启动")

    record = _load_latest_record()
    if record is None:
        print("[report] 未找到检索记录，请先执行主题检索")
        return

    topic = record.get("topic", "")
    print(f"[report] 生成主题「{topic}」的 8 段式报告...")

    # 复用内容分析 + 报告生成
    analysis = analysis_service.analyze(record["items"])
    report_id, report_md = report_service.generate_report(record, analysis)

    # 输出报告段落标题概览
    section_titles = [
        "事件概述", "时间线", "传播渠道", "主要观点",
        "情绪倾向", "风险判断", "重点证据", "结论摘要",
    ]
    print(f"[report] 报告编号：{report_id}")
    for title in section_titles:
        print(f"[report]  - {title}")

    print("[report] 报告生成完成")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
