# 舆情分析平台 · 接口说明与运行指南

> 对应开发文档 T14 交付。本文档汇总全部已实现接口、运行方式与验收说明。

---

## 1. 环境准备

### 1.1 依赖安装

```powershell
pip install -r requirements.txt
```

### 1.2 配置

复制环境变量模板（可选，默认即可离线运行）：

```powershell
Copy-Item .env.example .env
```

关键配置项（`.env`）：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | mysql+pymysql://... | MySQL 连接（当前落库为降级可选，未连接不影响核心流程） |
| `REDIS_URL` | redis://localhost:6379/0 | Redis（Celery 用，当前同步模式不强依赖） |
| `LLM_API_KEY` | 空 | 留空走规则引擎离线模式 |
| `REPO_BACKEND` | mysql | 仓储后端（预留） |

### 1.3 数据库迁移（可选）

```powershell
alembic upgrade head
```

> 未执行迁移不影响检索/分析/报告/图谱核心流程（落库为降级可选）。

### 1.4 启动服务

```powershell
uvicorn app.main:app --reload
```

- 服务地址：`http://127.0.0.1:8000`
- 接口文档（自动生成）：`http://127.0.0.1:8000/docs`

---

## 2. 接口清单

### 2.1 统一约定

- 响应格式：`{"code": 0, "message": "success", "data": {...}}`
- 错误码：`1001` 参数错误、`1002` 不存在、`2001` 状态不允许、`4001` 任务失败、`5001` 内部错误

### 2.2 接口明细

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| GET | `/api/health` | 健康检查 | - |
| GET | `/api/status` | 各应用运行状态 | - |
| GET | `/api/start/{app_name}` | 启动单功能应用 | - |
| GET | `/api/stop/{app_name}` | 停止单功能应用 | - |
| GET | `/api/output/{app_name}` | 应用最近输出 | - |
| GET | `/api/test_log/{app_name}` | 应用测试日志 | - |
| POST | `/api/search` | 主题检索与分析 | `{query, source_types}` |
| GET | `/api/forum/start` | 启动论坛采集 | - |
| GET | `/api/forum/stop` | 停止论坛采集 | - |
| GET | `/api/forum/log` | 论坛最新日志 | - |
| POST | `/api/forum/log/history` | 论坛历史日志 | `{date}` |
| GET | `/api/config` | 查询配置 | - |
| POST | `/api/config` | 更新配置 | `{version, ...}` |
| GET | `/api/system/status` | 系统状态 | - |
| POST | `/api/system/start` | 启动系统 | - |
| POST | `/api/system/shutdown` | 关闭系统 | - |
| GET | `/api/graph/latest` | 最新图谱 | - |
| GET | `/api/graph/{report_id}` | 指定报告图谱 | - |
| POST | `/api/graph/query` | 图谱关系查询 | `{report_id, node_id?, relation_type?}` |
| WS | `/ws` | 实时消息推送 | - |

---

## 3. 调用示例（PowerShell）

> 注意：PowerShell 中 `curl` 是 `Invoke-WebRequest` 别名，POST 请用 `Invoke-RestMethod` 或 `curl.exe`。

```powershell
# 健康检查
Invoke-RestMethod http://127.0.0.1:8000/api/health

# 主题检索
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/search -ContentType "application/json" -Body '{"query":"新品","source_types":["internal_data"]}'

# 查看图谱
Invoke-RestMethod http://127.0.0.1:8000/api/graph/latest

# 启动系统
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/system/start
```

---

## 4. 端到端演示

```powershell
python scripts/demo.py
```

演示脚本自动执行「检索 → 分析 → 报告 → 图谱查询」完整链路。

---

## 5. 文件产物说明

| 目录 | 内容 |
|------|------|
| `reports/{report_id}/report.md` | 结构化分析报告（8 节） |
| `graphs/{report_id}/graph.json` | 图谱节点与边 |
| `runtime/forum/latest.log` | 论坛最新日志 |
| `runtime/forum/history/{date}.json` | 论坛历史归档 |
| `outputs/{app}/latest.txt` | 应用最近输出 |
| `runtime/apps/{app}.log` | 应用日志 |

---

## 6. 已实现与占位说明

- **已实现**：控制层、进程管理（内存状态）、检索分析（规则模式）、报告、图谱、论坛（模拟）、系统启停、WebSocket、配置。
- **占位/模拟**：公开信息采集、论坛真实抓取、情绪词典（精简）、LLM 增强。详见 `未实现功能说明.md`。

---

## 7. 验收对照（需求 2.2.12）

| 验收项 | 状态 |
|--------|------|
| 启动/停止单功能应用 | ✅ |
| 查看应用状态/输出/错误 | ✅ |
| 论坛采集 + 日志/历史 | ✅ |
| 主题检索 + 结构化结果 | ✅ |
| 最新/指定图谱 + 关系查询 | ✅ |
| 配置更新即时生效 | ✅ |
| 完整主题案例演示 | ✅ |
