# 示例数据

本目录提供一个完整主题「MCP 协议发布」的舆情分析示例数据，用于验收演示。

## 目录说明

```
examples/
├── README.md                       # 本说明
├── mcp_20260826090000/
│   ├── sources.json                # 来源数据（三方向采集结果）
│   ├── report.md                   # 8 段式分析报告
│   └── graph.json                  # 图谱数据
```

## 使用方式

1. 将 `examples/mcp_20260826090000/` 下的 `report.md`、`graph.json` 分别复制到
   `data/reports/mcp_20260826090000/` 和 `data/graphs/mcp_20260826090000/`。
2. 启动后端服务，访问 `/api/graph/mcp_20260826090000` 查看图谱，
   或在控制台前端「图谱查看」页切换报告。
