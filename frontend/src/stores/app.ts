// 应用状态 Store：各应用状态与输出
import { defineStore } from 'pinia'
import { getOutput, getStatus, startApp, stopApp } from '@/api'

export const useAppStore = defineStore('app', {
  state: () => ({
    apps: {} as Record<string, string>,
    outputs: {} as Record<string, string>,
  }),
  getters: {
    appNames(state): string[] {
      return Object.keys(state.apps)
    },
  },
  actions: {
    async fetchStatus() {
      const data = await getStatus()
      this.apps = data.apps || {}
    },
    async start(name: string) {
      await startApp(name)
      this.apps[name] = 'running'
    },
    async stop(name: string) {
      await stopApp(name)
      this.apps[name] = 'stopped'
    },
    async fetchOutput(name: string) {
      const data = await getOutput(name)
      this.outputs[name] = data.output_text
    },
    // WebSocket 消息处理
    handleStatus(app_name: string, status: string) {
      this.apps[app_name] = status
    },
    handleOutput(app_name: string, output_text: string) {
      if (!this.outputs[app_name]) this.outputs[app_name] = ''
      this.outputs[app_name] += output_text
    },
  },
})
