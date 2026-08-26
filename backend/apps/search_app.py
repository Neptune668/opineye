"""主题检索应用（单功能应用子进程入口）。

启动后执行一次完整的检索分析流水线：
检索 → 内容分析 → 洞察 → 报告生成 → 图谱生成
复用 services 层真实逻辑，输出结果到 stdout（由 ProcessManager 采集）。
"""
from __future__ import annotations

import asyncio
import sys

from app.services import analysis_service, graph_service, report_service, search_service


async def main() -> None:
    # 默认主题与来源（可后续通过参数传递）
    topic = "舆情分析示例主题"
    source_types = ["news", "forum_post", "internal_data"]

    print(f"[search] 开始检索主题：{topic}")
    print(f"[search] 来源类型：{', '.join(source_types)}")

    # 1. 检索
    record = await search_service.search(topic, source_types)
    print(f"[search] 检索完成，来源条目 {len(record['items'])} 条")

    # 2. 内容分析
    analysis = analysis_service.analyze(record["items"])
    print(f"[search] 情绪整体判断：{analysis['overall_sentiment']}")

    # 3. 报告生成
    report_id, report_md = report_service.generate_report(record, analysis)
    print(f"[search] 报告已生成：{report_id}")

    # 4. 图谱生成
    graph = graph_service.generate_graph(report_id, record)
    graph_path = graph_service.save_graph(report_id, graph)
    print(f"[search] 图谱已生成：{graph_path}")
    print(f"[search] 图谱节点数：{len(graph['nodes'])}，关系数：{len(graph['edges'])}")

    print("[search] 检索分析流水线执行完成")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
