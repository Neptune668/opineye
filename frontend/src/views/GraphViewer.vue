<script setup lang="ts">
// 图谱查看页：最新/指定报告图谱 + 节点/关系查询
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import { GitNetworkOutline, SearchOutline, InformationCircleOutline } from '@vicons/ionicons5'
import GraphCanvas from '@/components/GraphCanvas.vue'
import { useGraphStore } from '@/stores/graph'

const route = useRoute()
const graphStore = useGraphStore()

const queryNode = ref('')
const queryRelation = ref('')
const selectedNode = ref('')
const loadError = ref('')

const selectedNodeDetail = computed(() => {
  if (!selectedNode.value || !graphStore.graphData) return null
  return graphStore.graphData.nodes.find((n) => n.id === selectedNode.value) || null
})

function onNodeClick(nodeId: string) {
  selectedNode.value = nodeId
}

onMounted(async () => {
  try {
    const reportId = route.params.report_id as string | undefined
    if (reportId) {
      await graphStore.fetchById(reportId)
    } else {
      await graphStore.fetchLatest()
    }
    loadError.value = ''
  } catch (e) {
    loadError.value = (e as Error).message || '图谱加载失败'
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
    <!-- 图谱主面板 -->
    <div class="panel graph-panel">
      <div class="panel-head">
        <div class="head-left">
          <n-icon :component="GitNetworkOutline" :size="20" color="#4f6ef7" />
          <span>关系图谱</span>
        </div>
        <n-tag type="info" round>{{ graphStore.currentReportId || '无报告' }}</n-tag>
      </div>

      <n-alert v-if="loadError" type="warning" style="margin-bottom: 12px">
        {{ loadError }}，请先在「主题检索」页发起一次检索生成图谱。
      </n-alert>
      <GraphCanvas v-else :graph="graphStore.graphData" @node-click="onNodeClick" />
    </div>

    <div class="side-col">
      <!-- 节点详情 -->
      <div v-if="selectedNodeDetail" class="panel">
        <div class="panel-head">
          <div class="head-left">
            <n-icon :component="InformationCircleOutline" :size="18" color="#4f6ef7" />
            <span>节点详情</span>
          </div>
        </div>
        <n-descriptions bordered :column="1" size="small">
          <n-descriptions-item label="ID">{{ selectedNodeDetail.id }}</n-descriptions-item>
          <n-descriptions-item label="标签">{{ selectedNodeDetail.label }}</n-descriptions-item>
          <n-descriptions-item label="类型">{{ selectedNodeDetail.type }}</n-descriptions-item>
          <n-descriptions-item label="来源引用">{{ selectedNodeDetail.source_ref }}</n-descriptions-item>
        </n-descriptions>
      </div>

      <!-- 图谱查询 -->
      <div class="panel">
        <div class="panel-head">
          <div class="head-left">
            <n-icon :component="SearchOutline" :size="18" color="#4f6ef7" />
            <span>图谱查询</span>
          </div>
        </div>
        <n-space vertical>
          <n-input v-model:value="queryNode" placeholder="节点关键词" />
          <n-input v-model:value="queryRelation" placeholder="关系类型，如 sourced_from" />
          <n-button type="primary" block @click="onQuery">
            <template #icon><n-icon :component="SearchOutline" /></template>
            查询
          </n-button>
        </n-space>
        <div v-if="graphStore.queryNodes.length" class="query-result">
          <n-tag
            v-for="n in graphStore.queryNodes"
            :key="n.id"
            size="small"
            round
            class="query-tag"
          >
            {{ n.label }}
          </n-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-viewer {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 20px;
  align-items: start;
}
.panel {
  background: #fff;
  border-radius: 14px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(31, 41, 55, 0.05);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f2f5;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}
.side-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.query-result {
  margin-top: 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.query-tag {
  margin: 0;
}
@media (max-width: 1000px) {
  .graph-viewer {
    grid-template-columns: 1fr;
  }
}
</style>
