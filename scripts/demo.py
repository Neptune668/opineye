"""端到端演示脚本：验证「检索 → 分析 → 报告 → 图谱」完整链路。

用法：
    python scripts/demo.py [query]

依赖服务已启动（uvicorn app.main:app）。默认主题「新品」。
"""

from __future__ import annotations

import sys

import requests

BASE_URL = "http://127.0.0.1:8000"


def main() -> None:
    query = sys.argv[1] if len(sys.argv) > 1 else "新品"
    print(f"=== 主题检索演示：{query} ===")

    # 1. 发起主题检索
    print("\n[1] 发起主题检索 POST /api/search")
    r = requests.post(
        f"{BASE_URL}/api/search",
        json={"query": query, "source_types": ["internal_data"]},
    )
    r.raise_for_status()
    data = r.json()["data"]
    report_id = data["report"]["report_id"]
    print(f"  task_id   = {data['task_id']}")
    print(f"  report_id = {report_id}")

    analysis = data["analysis"]
    print(f"  概述       = {analysis['overview'][:50]}...")
    print(f"  情绪       = {analysis['sentiment']['overall']}"
          f"（正{analysis['sentiment']['positive']}/中{analysis['sentiment']['neutral']}/负{analysis['sentiment']['negative']}）")
    print(f"  渠道分布   = {analysis['channels']}")
    print(f"  风险       = {analysis['risks']}")

    # 2. 查看报告文件
    print(f"\n[2] 报告文件路径 = {data['report']['file_path']}")

    # 3. 查看图谱
    print("\n[3] 查看指定报告图谱 GET /api/graph/{report_id}")
    r = requests.get(f"{BASE_URL}/api/graph/{report_id}")
    r.raise_for_status()
    g = r.json()["data"]
    print(f"  节点数 = {len(g['nodes'])}，边数 = {len(g['edges'])}")
    for n in g["nodes"][:5]:
        print(f"    - [{n['node_type']}] {n['label']}")

    # 4. 图谱关系查询
    print("\n[4] 图谱关系查询 POST /api/graph/query (node_id=topic)")
    r = requests.post(
        f"{BASE_URL}/api/graph/query",
        json={"report_id": report_id, "node_id": "topic"},
    )
    r.raise_for_status()
    q = r.json()["data"]
    print(f"  查询结果：节点 {len(q['nodes'])}，边 {len(q['edges'])}")

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
