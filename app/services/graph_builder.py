"""图谱构建器：从分析结果生成图谱节点与边。

规则：以主题词为中心节点，来源作为子节点，来源类型作为关系标签，
情绪倾向、关键词作为附加节点。保证报告结论可追溯到来源（ref 引用）。
"""

from __future__ import annotations

from app.analysis.models import AnalysisOutput
from app.services.graph_service import GraphData, GraphEdge, GraphNode


def build_graph(report_id: str, topic: str, analysis: AnalysisOutput) -> GraphData:
    """构建图谱数据。"""
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []

    # 中心节点：主题
    topic_node = GraphNode(node_id="topic", node_type="topic", label=topic)
    nodes.append(topic_node)

    # 情绪节点
    senti_node = GraphNode(
        node_id="sentiment", node_type="sentiment", label=f"情绪:{analysis.sentiment.overall}"
    )
    nodes.append(senti_node)
    edges.append(GraphEdge(source="topic", target="sentiment", relation_type="has_sentiment"))

    # 渠道节点 + 来源节点
    for idx, ev in enumerate(analysis.evidence):
        source_node_id = f"src_{idx}"
        source_node = GraphNode(
            node_id=source_node_id, node_type="source", label=ev.title, ref=ev.ref
        )
        nodes.append(source_node)
        edges.append(
            GraphEdge(source="topic", target=source_node_id, relation_type="mentioned_by", ref=ev.ref)
        )

    # 关键词节点
    for kw in _extract_keywords_from_overview(analysis.overview):
        kw_node_id = f"kw_{kw}"
        nodes.append(GraphNode(node_id=kw_node_id, node_type="keyword", label=kw))
        edges.append(GraphEdge(source="topic", target=kw_node_id, relation_type="has_keyword"))

    return GraphData(report_id=report_id, nodes=nodes, edges=edges)


def _extract_keywords_from_overview(overview: str) -> list[str]:
    """从概述文本中提取关键词（简化：取「涉及关键词：」后的内容）。"""
    marker = "涉及关键词："
    if marker not in overview:
        return []
    kw_part = overview.split(marker, 1)[1].split("。")[0]
    return [k.strip() for k in kw_part.split("、") if k.strip()]
