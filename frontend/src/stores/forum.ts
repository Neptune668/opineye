// 论坛 Store：采集状态与日志
import { defineStore } from 'pinia'
import { forumHistory, forumLog, forumStart, forumStop } from '@/api'
import type { ForumHistoryEntry } from '@/types'

export const useForumStore = defineStore('forum', {
  state: () => ({
    taskStatus: 'idle' as string,
    logLines: [] as string[],
    history: [] as ForumHistoryEntry[],
  }),
  actions: {
    async start() {
      const data = await forumStart()
      this.taskStatus = data.task_status
    },
    async stop() {
      const data = await forumStop()
      this.taskStatus = data.task_status
    },
    async fetchLog(tail = 200) {
      const data = await forumLog(tail)
      this.logLines = data.lines || []
    },
    async fetchHistory(date: string) {
      const data = await forumHistory(date)
      this.history = data.entries || []
    },
    // WebSocket 消息处理
    handleLog(message_text: string, task_status: string) {
      this.logLines.push(message_text)
      this.taskStatus = task_status
    },
  },
})
