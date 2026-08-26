<script setup lang="ts">
// 图谱查看页：最新/指定报告图谱 + 节点/关系查询
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import GraphCanvas from '@/components/GraphCanvas.vue'
import { useGraphStore } from '@/stores/graph'

const route = useRoute()
const graphStore = useGraphStore()

const queryNode = ref('')
const queryRelation = ref('')
const selectedNode = ref('')

const selectedNodeDetail = computed(() => {
  if (!selectedNode.value || !graphStore.graphData) return null
  return graphStore.graphData.nodes.find((n) => n.id === selectedNode.value) || null
})

function onNodeClick(nodeId: string) {
  selectedNode.value = nodeId
}

onMounted(async () => {
  const reportId = route.params.report_id as string | undefined
  if (reportId) {
    await graphStore.fetchById(reportId)
  } else {
    await graphStore.fetchLatest()
  }
})

async function onQuery() {
  await graphStore.query({
    report_id: graphStore.currentReportId || undefined,
    node: queryNode.value || undefined,
    relation: queryRelation.value || undefined,
  })
}
</script>

<template>
  <div class="graph-viewer">
    <n-space vertical :size="16">
      <n-card title="图谱" size="small">
        <template #header-extra>
          <n-tag type="info">{{ graphStore.currentReportId || '无报告' }}</n-tag>
        </template>
        <GraphCanvas :graph="graphStore.graphData" @node-click="onNodeClick" />
      </n-card>

      <n-card title="节点详情" size="small" v-if="selectedNodeDetail">
        <n-descriptions bordered :column="1" size="small">
          <n-descriptions-item label="ID">{{ selectedNodeDetail.id }}</n-descriptions-item>
          <n-descriptions-item label="标签">{{ selectedNodeDetail.label }}</n-descriptions-item>
          <n-descriptions-item label="类型">{{ selectedNodeDetail.type }}</n-descriptions-item>
          <n-descriptions-item label="来源引用">{{ selectedNodeDetail.source_ref }}</n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="图谱查询" size="small">
        <n-space>
          <n-input v-model:value="queryNode" placeholder="节点关键词" style="width: 160px" />
          <n-input v-model:value="queryRelation" placeholder="关系类型" style="width: 160px" />
          <n-button size="small" type="primary" @click="onQuery">查询</n-button>
        </n-space>
        <div v-if="graphStore.queryNodes.length" style="margin-top: 12px">
          <n-tag v-for="n in graphStore.queryNodes" :key="n.id" size="small" style="margin: 4px">
            {{ n.label }}
          </n-tag>
        </div>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.graph-viewer {
  padding: 16px;
}
</style>
