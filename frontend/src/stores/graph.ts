// 图谱 Store：当前图谱数据与报告编号
import { defineStore } from 'pinia'
import { graphById, graphLatest, graphQuery } from '@/api'
import type { GraphData, GraphNode, GraphEdge } from '@/types'

export const useGraphStore = defineStore('graph', {
  state: () => ({
    graphData: null as GraphData | null,
    currentReportId: '' as string,
    queryNodes: [] as GraphNode[],
    queryEdges: [] as GraphEdge[],
  }),
  actions: {
    async fetchLatest() {
      const data = await graphLatest()
      this.graphData = data.graph
      this.currentReportId = data.report_id
    },
    async fetchById(reportId: string) {
      const data = await graphById(reportId)
      this.graphData = data.graph
      this.currentReportId = data.report_id
    },
    async query(body: { report_id?: string; node?: string; relation?: string }) {
      const data = await graphQuery(body)
      this.queryNodes = data.nodes || []
      this.queryEdges = data.edges || []
    },
    // WebSocket 消息处理
    handleGraphReady(report_id: string) {
      this.currentReportId = report_id
    },
  },
})
