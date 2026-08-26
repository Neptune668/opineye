// 系统状态 Store：整体状态、错误、资源概况
import { defineStore } from 'pinia'
import { systemShutdown, systemStart, systemStatus } from '@/api'

export const useSystemStore = defineStore('system', {
  state: () => ({
    systemStatus: 'online' as string,
    runningApps: {} as Record<string, string>,
    errors: [] as string[],
  }),
  actions: {
    async fetchStatus() {
      const data = await systemStatus()
      this.systemStatus = data.system_status
      this.runningApps = data.running_apps || {}
      this.errors = data.errors || []
    },
    async start() {
      const data = await systemStart()
      this.systemStatus = data.system_status
    },
    async shutdown() {
      const data = await systemShutdown()
      this.systemStatus = data.system_status
    },
    // WebSocket 消息处理
    handleSystemStatus(system_status: string, running_apps: string[]) {
      this.systemStatus = system_status
      this.runningApps = running_apps.reduce((acc, name) => {
        acc[name] = 'running'
        return acc
      }, {} as Record<string, string>)
    },
    handleError(module_name: string, error_message: string) {
      this.errors.push(`[${module_name}] ${error_message}`)
    },
  },
})
