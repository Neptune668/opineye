"""主题检索服务：三方向并行采集 + 落盘来源数据。

query + source_types → 并行采集三方向（公开信息/多媒体/内部数据）
→ 返回结构化来源条目列表，供分析/报告/图谱使用。
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from app import settings
from app.core import store

logger = logging.getLogger(__name__)

# 来源类型 → 采集方向映射
_SOURCE_GROUPS = {
    "news": "公开信息",
    "image": "多媒体",
    "video": "多媒体",
    "forum_post": "论坛",
    "internal_data": "内部沉淀数据",
}


def _generate_report_id(topic: str) -> str:
    """生成 report_id：{主题词拼音缩写}_{YYYYMMDDHHmmss}。

    拼音缩写简化为：取主题前 N 个字符的 ASCII 安全形式，非 ASCII 回退为 'topic'。
    """
    import re as _re

    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    # 提取主题中的 ASCII 字母数字作为缩写，非 ASCII 主题回退为 'topic'
    alpha = _re.sub(r"[^a-zA-Z0-9]", "", topic)
    abbr = (alpha[:6] or "topic").lower()
    return f"{abbr}_{stamp}"


async def _collect_source(source_type: str, query: str) -> list[dict[str, Any]]:
    """采集单个来源类型的数据。

    当前为确定性模拟采集（示例数据逻辑），后续可替换为真实采集。
    """
    # 模拟异步采集耗时
    await asyncio.sleep(0.01)
    group = _SOURCE_GROUPS.get(source_type, "公开信息")
    return [
        {
            "source_type": source_type,
            "group": group,
            "title": f"【{source_type}】关于「{query}」的来源样本",
            "text": _sample_text(source_type, query),
            "url": f"https://example.com/{source_type}/{query}",
            "collected_at": datetime.now().isoformat(),
        }
        for _ in range(3)
    ]


def _sample_text(source_type: str, query: str) -> str:
    """生成带情绪倾向的样本文本（演示用，含规则词典关键词）。"""
    samples = {
        "news": f"多家媒体关注「{query}」，报道总体正面，公众普遍支持并认可其进展。",
        "image": f"关于「{query}」的图片内容在社交平台传播，评论区好评如潮。",
        "video": f"「{query}」相关视频播放量较高，观众表达满意与喜爱。",
        "forum_post": f"论坛用户讨论「{query}」，部分网友提出质疑与担忧，存在负面声音。",
        "internal_data": f"内部沉淀数据显示「{query}」近期出现风险隐患，需重点关注。",
    }
    return samples.get(source_type, f"关于「{query}」的一般性内容。")


async def search(query: str, source_types: list[str]) -> dict[str, Any]:
    """执行主题检索，返回报告元信息与来源条目。"""
    # 并行采集三方向
    results = await asyncio.gather(
        *[_collect_source(st, query) for st in source_types]
    )
    items: list[dict[str, Any]] = [item for group in results for item in group]

    report_id = _generate_report_id(query)
    record = {
        "report_id": report_id,
        "topic": query,
        "executed_at": datetime.now().isoformat(),
        "source_types": source_types,
        "source_summary": [
            {"source_type": st, "count": sum(1 for it in items if it["source_type"] == st)}
            for st in source_types
        ],
        "items": items,
    }

    # 落盘来源数据到 reports/{report_id}/sources.json
    report_dir = settings.REPORTS_DIR / report_id
    report_dir.mkdir(parents=True, exist_ok=True)
    store.write_json(report_dir / "sources.json", record)
    logger.info("检索完成：%s，来源条目 %d 条", report_id, len(items))

    return record
