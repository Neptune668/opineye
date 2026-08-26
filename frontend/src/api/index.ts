// Axios 实例 + 接口封装
import axios from 'axios'
import type {
  ApiResponse,
  AppStatusData,
  ConfigData,
  ForumHistoryEntry,
  ForumLogData,
  GraphData,
  OutputData,
  SearchRequest,
  SearchResult,
  StatusData,
  SystemStatusData,
  TestLogData,
} from '@/types'

const instance = axios.create({
  baseURL: '',
  timeout: 15000,
})

// 响应拦截器：统一处理 code
instance.interceptors.response.use(
  (response) => {
    const body = response.data as ApiResponse
    if (body && typeof body.code === 'number' && body.code !== 0) {
      return Promise.reject(new Error(body.message || '请求失败'))
    }
    return response
  },
  (error) => {
    const message = error?.response?.data?.detail || error.message || '网络错误'
    return Promise.reject(new Error(message))
  },
)

async function get<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const res = await instance.get<ApiResponse<T>>(url, { params })
  return res.data.data
}

async function post<T>(url: string, body?: unknown): Promise<T> {
  const res = await instance.post<ApiResponse<T>>(url, body)
  return res.data.data
}

// ---- 状态 ----
export const getStatus = () => get<StatusData>('/api/status')
export const startApp = (appName: string) => get<AppStatusData>(`/api/start/${appName}`)
export const stopApp = (appName: string) => get<AppStatusData>(`/api/stop/${appName}`)
export const getOutput = (appName: string) => get<OutputData>(`/api/output/${appName}`)
export const getTestLog = (appName: string, tail = 200) =>
  get<TestLogData>(`/api/test_log/${appName}`, { tail })

// ---- 检索 ----
export const search = (body: SearchRequest) => post<SearchResult>('/api/search', body)

// ---- 论坛 ----
export const forumStart = () => get<{ task_status: string }>('/api/forum/start')
export const forumStop = () => get<{ task_status: string }>('/api/forum/stop')
export const forumLog = (tail = 200) => get<ForumLogData>('/api/forum/log', { tail })
export const forumHistory = (date: string) =>
  post<{ entries: ForumHistoryEntry[] }>('/api/forum/log/history', { date })

// ---- 图谱 ----
export const graphLatest = () => get<{ report_id: string; graph: GraphData }>('/api/graph/latest')
export const graphById = (reportId: string) =>
  get<{ report_id: string; graph: GraphData }>(`/api/graph/${reportId}`)
export const graphQuery = (body: { report_id?: string; node?: string; relation?: string }) =>
  post<{ nodes: GraphData['nodes']; edges: GraphData['edges'] }>('/api/graph/query', body)

// ---- 配置 ----
export const getConfig = () => get<ConfigData>('/api/config')
export const updateConfig = (config: Record<string, unknown>) =>
  post<ConfigData>('/api/config', { config })

// ---- 系统 ----
export const systemStatus = () => get<SystemStatusData>('/api/system/status')
export const systemStart = () => post<{ system_status: string }>('/api/system/start')
export const systemShutdown = () => post<{ system_status: string }>('/api/system/shutdown')
