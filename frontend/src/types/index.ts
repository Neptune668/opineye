// API 响应、WebSocket 消息、Store 状态类型定义

// ---- 通用 API 响应 ----
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

// ---- 状态相关 ----
export interface StatusData {
  system_status: string
  apps: Record<string, string>
}

export interface AppStatusData {
  app_name: string
  status: string
}

export interface OutputData {
  app_name: string
  output_text: string
}

export interface TestLogData {
  app_name: string
  lines: string[]
}

// ---- 检索相关 ----
export interface SearchRequest {
  query: string
  source_types: string[]
}

export interface SearchResult {
  report_id: string
  report_md: string
  graph_path: string
}

// ---- 论坛相关 ----
export interface ForumLogData {
  lines: string[]
}

export interface ForumHistoryEntry {
  time: string
  event: string
  message: string
  task_status: string
}

// ---- 图谱相关 ----
export interface GraphNode {
  id: string
  label: string
  type: string
  source_ref: string
}

export interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  source_ref: string
}

export interface GraphData {
  report_id: string
  meta: { generated_at: string; topic: string }
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ---- 配置 ----
export interface ConfigData {
  config: Record<string, unknown>
}

// ---- WebSocket 消息 ----
export interface WsMessage {
  type: string
  data: Record<string, unknown>
  ts?: number
}

// ---- 系统状态 ----
export interface SystemStatusData {
  system_status: string
  running_apps: Record<string, string>
  errors: string[]
}
