<script setup lang="ts">
// 应用状态卡片：展示单个应用状态与启停按钮
import { computed } from 'vue'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ appName: string }>()
const appStore = useAppStore()

const status = computed(() => appStore.apps[props.appName] || 'stopped')

const statusType = computed(() => {
  switch (status.value) {
    case 'running':
      return 'success'
    case 'failed':
      return 'error'
    case 'starting':
    case 'stopping':
      return 'warning'
    default:
      return 'default'
  }
})

const statusText = computed(() => {
  const map: Record<string, string> = {
    stopped: '已停止',
    starting: '启动中',
    running: '运行中',
    stopping: '停止中',
    failed: '异常',
  }
  return map[status.value] || status.value
})

const isRunning = computed(() => status.value === 'running')
const canStart = computed(() => status.value === 'stopped' || status.value === 'failed')
</script>

<template>
  <n-card :title="appName" size="small" class="app-card">
    <template #header-extra>
      <n-tag :type="statusType" size="small">{{ statusText }}</n-tag>
    </template>
    <div class="actions">
      <n-button
        size="small"
        type="primary"
        :disabled="!canStart"
        @click="appStore.start(appName)"
      >
        启动
      </n-button>
      <n-button
        size="small"
        type="error"
        :disabled="!isRunning"
        @click="appStore.stop(appName)"
      >
        停止
      </n-button>
    </div>
  </n-card>
</template>

<style scoped>
.actions {
  display: flex;
  gap: 8px;
}
</style>
