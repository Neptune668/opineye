<script setup lang="ts">
// ECharts graph 图谱封装：力导向布局，节点点击查看详情
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import type { GraphData } from '@/types'

const props = defineProps<{ graph: GraphData | null }>()
const emit = defineEmits<{ (e: 'node-click', nodeId: string): void }>()

const chartRef = ref<HTMLElement | null>(null)
let chart: echarts.ECharts | null = null

const NODE_TYPES = [
  { name: 'topic' },
  { name: 'person' },
  { name: 'org' },
  { name: 'event' },
  { name: 'source' },
  { name: 'keyword' },
]

function typeIndex(type: string): number {
  const idx = NODE_TYPES.findIndex((t) => t.name === type)
  return idx >= 0 ? idx : 5
}

function render() {
  if (!chart || !props.graph) return
  const { nodes, edges } = props.graph
  chart.setOption({
    tooltip: { show: true },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: nodes.map((n) => ({
          id: n.id,
          name: n.label,
          category: typeIndex(n.type),
        })),
        links: edges.map((e) => ({
          source: e.source,
          target: e.target,
          label: { show: true, formatter: e.type },
        })),
        categories: NODE_TYPES,
        roam: true,
        label: { show: true, position: 'right' },
        emphasis: { focus: 'adjacency' },
        force: { repulsion: 300, edgeLength: 120 },
      },
    ],
  })
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
    render()
  }
})

watch(() => props.graph, render, { deep: true })

onBeforeUnmount(() => {
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
  height: 520px;
}
</style>
