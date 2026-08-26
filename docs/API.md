# 舆情分析平台 API 接口说明

> 统一前缀 `/api`，返回结构 `{ "code": 0, "message": "ok", "data": {...} }`
> `code != 0` 表示错误，`message` 为错误说明。

## 1. 状态接口

### GET /api/status
控制台状态 + 各应用状态。

返回 `data`：
```json
{ "system_status": "online", "apps": { "search": "stopped", "media": "stopped" } }
```

### GET /api/start/{app_name}
启动单功能应用。`app_name` 仅允许小写字母与下划线。

返回 `data`：`{ "app_name": "search", "status": "running" }`

### GET /api/stop/{app_name}
停止单功能应用。

返回 `data`：`{ "app_name": "search", "status": "stopped" }`

### GET /api/output/{app_name}
应用最近输出。

返回 `data`：`{ "app_name": "search", "output_text": "..." }`

### GET /api/test_log/{app_name}?tail=200
应用测试日志（尾部）。

返回 `data`：`{ "app_name": "search", "lines": ["...", "..."] }`

## 2. 检索接口

### POST /api/search
主题检索 + 分析 + 报告 + 图谱一站式流程。

请求体：
```json
{ "query": "某产品发布", "source_types": ["news", "forum_post", "internal_data"] }
```

返回 `data`：
```json
{ "report_id": "topic_20260826102831", "report_md": "...", "graph_path": "..." }
```

## 3. 论坛接口

### GET /api/forum/start
启动论坛采集。返回 `data`：`{ "task_status": "running" }`

### GET /api/forum/stop
停止论坛采集。返回 `data`：`{ "task_status": "stopped" }`

### GET /api/forum/log?tail=200
论坛最新日志。返回 `data`：`{ "lines": ["..."] }`

### POST /api/forum/log/history
按日期查询历史日志。请求体 `{ "date": "2026-08-26" }`

返回 `data`：
```json
{ "entries": [ { "time": "...", "event": "collect", "message": "...", "task_status": "running" } ] }
```

## 4. 配置接口

### GET /api/config
查询系统配置。返回 `data`：`{ "config": {...} }`

### POST /api/config
更新配置（热更新，自动备份 config.json.bak）。请求体 `{ "config": {...} }`

## 5. 系统接口

### GET /api/system/status
整体服务状态。返回 `data`：`{ "system_status": "online", "running_apps": {...}, "errors": [] }`

### POST /api/system/start
启动整体服务（默认启动 default_apps）。返回 `data`：`{ "system_status": "online" }`

### POST /api/system/shutdown
关闭整体服务。返回 `data`：`{ "system_status": "offline" }`

## 6. 图谱接口

### GET /api/graph/latest
最新图谱。返回 `data`：`{ "report_id": "...", "graph": {...} }`

### GET /api/graph/{report_id}
指定报告图谱。不存在返回 404。

### POST /api/graph/query
按节点/关系查询图谱。请求体 `{ "report_id": "...", "node": "关键词", "relation": "sourced_from" }`

返回 `data`：`{ "nodes": [...], "edges": [...] }`

### GET /graph-viewer、/graph-viewer/{report_id}
图谱查看页（SPA 路由回退）。

## 7. WebSocket 实时协议

- 连接地址：`/ws`
- 消息信封：`{ "type": "...", "data": {...}, "ts": 1234567890 }`

| type | data 字段 | 触发时机 |
| ---- | --------- | -------- |
| `app_status` | `app_name`, `status` | 应用状态变更 |
| `app_output` | `app_name`, `output_text` | 应用输出流 |
| `forum_log` | `message_text`, `task_status` | 论坛日志新增 |
| `system_status` | `system_status`, `running_apps` | 系统状态变化 |
| `graph_ready` | `report_id`, `graph_path` | 图谱生成完成 |
| `error` | `module_name`, `error_message` | 模块出错 |
| `heartbeat` | — | 服务端心跳（30s） |

客户端收到 `heartbeat` 后回复 `{ "type": "heartbeat_ack" }`。

## 8. 状态枚举

- **应用状态**：`stopped` / `starting` / `running` / `stopping` / `failed`
- **论坛状态**：`idle` / `running` / `stopped` / `failed`
- **系统状态**：`offline` / `starting` / `online` / `shutting_down`
- **来源类型**：`news` / `image` / `video` / `forum_post` / `internal_data`
