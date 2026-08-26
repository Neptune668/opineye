<script setup lang="ts">
// ECharts graph 图谱封装：力导向布局，节点点击查看详情
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { GraphData } from '@/types'

const props = defineProps<{ graph: GraphData | null }>()
const emit = defineEmits<{ (e: 'node-click', nodeId: string): void }>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

// 节点类型配色（与整体主题色呼应）
const NODE_TYPES = [
  { name: 'topic', itemStyle: { color: '#4f6ef7' } },
  { name: 'person', itemStyle: { color: '#18a058' } },
  { name: 'org', itemStyle: { color: '#f0a020' } },
  { name: 'event', itemStyle: { color: '#d03050' } },
  { name: 'source', itemStyle: { color: '#2080f0' } },
  { name: 'keyword', itemStyle: { color: '#7b5cf0' } },
]

const TYPE_LABELS: Record<string, string> = {
  topic: '主题',
  person: '人物',
  org: '机构',
  event: '事件',
  source: '来源',
  keyword: '关键词',
}

function typeIndex(type: string): number {
  const idx = NODE_TYPES.findIndex((t) => t.name === type)
  return idx >= 0 ? idx : 5
}

function render() {
  if (!chart || !props.graph) return
  const { nodes, edges } = props.graph
  chart.setOption({
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        if (p.dataType === 'node') {
          const t = nodes.find((n) => n.id === p.data.id)
          return `<b>${p.data.name}</b><br/>类型：${TYPE_LABELS[t?.type || ''] || t?.type}`
        }
        return `<b>${p.data.source}</b> → <b>${p.data.target}</b>`
      },
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes.map((n) => ({
          id: n.id,
          name: n.label,
          category: typeIndex(n.type),
          symbolSize: n.type === 'topic' ? 56 : 36,
        })),
        links: edges.map((e) => ({
          source: e.source,
          target: e.target,
          label: { show: true, formatter: e.type, fontSize: 10 },
        })),
        categories: NODE_TYPES,
        roam: true,
        label: { show: true, position: 'right', fontSize: 12, color: '#374151' },
        lineStyle: { color: '#cbd5e1', curveness: 0.1 },
        emphasis: {
          focus: 'adjacency',
          lineStyle: { width: 3, color: '#4f6ef7' },
        },
        force: { repulsion: 400, edgeLength: 140, gravity: 0.08 },
      },
    ],
  })
}

function handleResize() {
  chart?.resize()
}

onMounted(() => {
  if (chartRef.value) {
    chart = echarts.init(chartRef.value)
    chart.on('click', (params) => {
      if (params.dataType === 'node') {
        const data = params.data as { id: string } | null
        if (data && data.id) {
          emit('node-click', data.id)
        }
      }
    })
    window.addEventListener('resize', handleResize)
    render()
  }
})

watch(() => props.graph, render, { deep: true })

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})
</script>

<template>
  <div ref="chartRef" class="graph-canvas"></div>
</template>

<style scoped>
.graph-canvas {
  width: 100%;
  height: 560px;
  border-radius: 10px;
  background: #fafbfc;
}
</style>
