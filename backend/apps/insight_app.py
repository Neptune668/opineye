"""洞察分析应用（单功能应用子进程入口）。

启动后读取最新一次检索记录，生成洞察并输出。
"""
from __future__ import annotations

import asyncio
import sys

from app import settings
from app.core import store
from app.services import analysis_service, insight_service


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
    print("[insight] 洞察分析应用已启动")

    record = _load_latest_record()
    if record is None:
        print("[insight] 未找到检索记录，请先执行主题检索")
        return

    topic = record.get("topic", "")
    items = record.get("items", [])
    print(f"[insight] 分析主题：{topic}（来源条目 {len(items)} 条）")

    # 复用内容分析 + 洞察生成
    analysis = analysis_service.analyze(items)
    insights = insight_service.generate_insights(analysis)

    print(f"[insight] 情绪整体判断：{analysis['overall_sentiment']}")
    for ins in insights:
        print(f"[insight] {ins}")

    print("[insight] 洞察分析完成")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
