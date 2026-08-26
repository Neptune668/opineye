# 舆情分析平台 · 接口说明与运行指南

> 对应开发文档 T14 交付。本文档汇总全部已实现接口、运行方式与验收说明。

---

## 0. 快速开始

### 0.1 环境要求

- Python 3.11+
- （可选）MySQL、Redis —— 未安装不影响离线运行核心流程

### 0.2 启动步骤

```powershell
# 1. 激活虚拟环境（注意是 .venv，不是 venv）
.venv\Scripts\Activate.ps1

# 2. 安装依赖
pip install -r requirements.txt

# 3.（可选）配置环境变量
Copy-Item .env.example .env

# 4. 启动服务（前后端一体）
uvicorn app.main:app --reload
```

启动完成后访问：

| 地址 | 说明 |
|------|------|
| `http://127.0.0.1:8000/` | 前端控制台（Web 界面） |
| `http://127.0.0.1:8000/docs` | 后端接口文档（OpenAPI） |
| `http://127.0.0.1:8000/api/health` | 健康检查 |

> 本项目前后端一体部署，启动 uvicorn 后即可同时使用前端页面与后端接口，无需单独启动前端服务。

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
| `DATABASE_URL` | mysql+pymysql://... | MySQL 连接（落库，未连接则降级不影响核心流程） |
| `REDIS_URL` | redis://localhost:6379/0 | Redis（Celery 用，当前同步模式不强依赖） |
| `LLM_API_KEY` | 空 | LLM 分析增强（留空走规则引擎离线模式） |
| `LLM_BASE_URL` | 空 | LLM 接口地址 |
| `LLM_MODEL` | 空 | LLM 模型名 |
| `TAVILY_API_KEY` | 空 | Tavily 搜索（news 来源，留空回退 file 数据源） |
| `z_c0` | 空 | 知乎登录凭证（forum_post 来源热榜，留空回退 file 数据源） |
| `REPO_BACKEND` | mysql | 仓储后端（预留） |
| `SECRET_KEY` | change-me | JWT 签名密钥（生产环境务必修改） |

### 1.3 数据库迁移（可选）

```powershell
alembic upgrade head
```

> 未执行迁移不影响检索/分析/报告/图谱核心流程（落库为降级可选）。

### 1.4 启动服务

```powershell
uvicorn app.main:app --reload
```

- 前端控制台：`http://127.0.0.1:8000/`
- 接口文档（自动生成）：`http://127.0.0.1:8000/docs`

---

## 2. 前端控制台

前端使用原生 HTML/CSS/JS 实现，单页应用，共 6 个页面（对应需求 2.2.3）：

| 页面 | 功能 |
|------|------|
| 控制台首页 | 应用状态卡片、启动/停止/查看输出、系统启停 |
| 主题检索 | 输入主题词、选来源类型、展示结构化分析结果 |
| 论坛监控 | 启动/停止采集、最新日志、按日期查历史 |
| 图谱查看 | 最新图谱、按 report_id 加载、节点/关系展示 |
| 配置管理 | 读取/保存配置（JSON 编辑） |
| 系统状态 | 系统状态、运行中应用数、各应用状态 |

前端通过 WebSocket（`/ws`）实时接收 `app_status`/`system_status`/`forum_log` 消息并自动刷新。

---

## 3. 接口清单

### 3.1 统一约定

- 响应格式：`{"code": 0, "message": "success", "data": {...}}`
- 错误码：`1001` 参数错误、`1002` 不存在、`2001` 状态不允许、`4001` 任务失败、`5001` 内部错误

### 3.2 接口明细

| 方法 | 路径 | 说明 | 请求体 |
|------|------|------|--------|
| GET | `/api/health` | 健康检查（公开） | - |
| POST | `/api/register` | 注册操作用户（公开） | `{username, password}` |
| POST | `/api/login` | 登录获取 token（公开） | `{username, password}` |
| GET | `/api/status` | 各应用运行状态（user+） | - |
| GET | `/api/start/{app_name}` | 启动单功能应用（root） | - |
| GET | `/api/stop/{app_name}` | 停止单功能应用（root） | - |
| GET | `/api/output/{app_name}` | 应用最近输出（user+） | - |
| GET | `/api/test_log/{app_name}` | 应用测试日志（user+） | - |
| POST | `/api/search` | 主题检索与分析（user+） | `{query, source_types}` |
| GET | `/api/forum/start` | 启动论坛采集（root） | - |
| GET | `/api/forum/stop` | 停止论坛采集（root） | - |
| GET | `/api/forum/log` | 论坛最新日志（user+） | - |
| POST | `/api/forum/log/history` | 论坛历史日志（user+） | `{date}` |
| GET | `/api/config` | 查询配置（user+） | - |
| POST | `/api/config` | 更新配置（root） | `{version, ...}` |
| GET | `/api/system/status` | 系统状态（user+） | - |
| POST | `/api/system/start` | 启动系统（root） | - |
| POST | `/api/system/shutdown` | 关闭系统（root） | - |
| GET | `/api/graph/latest` | 最新图谱（user+） | - |
| GET | `/api/graph/{report_id}` | 指定报告图谱（user+） | - |
| POST | `/api/graph/query` | 图谱关系查询（user+） | `{report_id, node_id?, relation_type?}` |
| WS | `/ws` | 实时消息推送 | - |

---

## 4. 调用示例（PowerShell）

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

## 5. 端到端演示

```powershell
python scripts/demo.py
```

演示脚本自动执行「检索 → 分析 → 报告 → 图谱查询」完整链路。

---

## 6. 文件产物说明

| 目录 | 内容 |
|------|------|
| `reports/{report_id}/report.md` | 结构化分析报告（8 节） |
| `graphs/{report_id}/graph.json` | 图谱节点与边 |
| `runtime/forum/latest.log` | 论坛最新日志 |
| `runtime/forum/history/{date}.json` | 论坛历史归档 |
| `outputs/{app}/latest.txt` | 应用最近输出 |
| `runtime/apps/{app}.log` | 应用日志 |

---

## 7. 数据源与已实现说明

### 7.1 数据源

| 来源类型 | 数据源 | 说明 |
|----------|--------|------|
| `news` | Tavily 搜索 | 真实网络搜索，一次请求获取 15 条数据 |
| `forum_post` | 知乎热榜 | 真实热榜数据（需 `z_c0` Cookie） |
| `image` / `video` | 本地文件 | `data/image.json`、`data/video.json` |
| `internal_data` | 本地文件 | `data/internal_data.json`（内部沉淀数据） |

> 数据源均可通过 `config.json` 的 `datasources` 段配置；外部数据源不可用时自动回退本地文件数据。

### 7.2 鉴权说明

- 角色：`root`（系统管理员，内置账号，初始密码 1234）、`user`（报告人/操作用户，需注册）
- 认证：JWT token，登录后通过 `Authorization: Bearer {token}` 请求头传递
- 接口权限分级见「3.2 接口明细」中括号标注（`root` / `user+` / `公开`）

### 7.3 已实现能力

控制层、进程管理、检索分析、报告、图谱、论坛采集（知乎热榜）、系统启停、WebSocket、配置、RBAC 鉴权、LLM 分析增强均已实现。详见 `未实现功能说明.md`。

---

## 8. 验收对照（需求 2.2.12）

| 验收项 | 状态 |
|--------|------|
| 启动/停止单功能应用 | ✅ |
| 查看应用状态/输出/错误 | ✅ |
| 论坛采集 + 日志/历史 | ✅ |
| 主题检索 + 结构化结果 | ✅ |
| 最新/指定图谱 + 关系查询 | ✅ |
| 配置更新即时生效 | ✅ |
| 完整主题案例演示 | ✅ |
