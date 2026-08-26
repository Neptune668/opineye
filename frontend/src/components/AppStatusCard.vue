<script setup lang="ts">
// 应用状态卡片：展示单个应用状态与启停按钮
import { computed } from 'vue'
import { NIcon, NTag } from 'naive-ui'
import {
  SearchOutline,
  ImageOutline,
  ChatbubblesOutline,
  BulbOutline,
  DocumentTextOutline,
  Play,
  Stop,
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'

const props = defineProps<{ appName: string }>()
const appStore = useAppStore()

// 应用图标映射
const appIcons: Record<string, any> = {
  search: SearchOutline,
  media: ImageOutline,
  forum: ChatbubblesOutline,
  insight: BulbOutline,
  report: DocumentTextOutline,
}

const appLabels: Record<string, string> = {
  search: '主题检索',
  media: '多媒体检索',
  forum: '论坛采集',
  insight: '洞察分析',
  report: '报告生成',
}

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

const icon = computed(() => appIcons[props.appName] || SearchOutline)
</script>

<template>
  <div class="app-card" :class="`status-${status}`">
    <div class="card-top">
      <div class="app-icon">
        <n-icon :component="icon" :size="22" />
      </div>
      <n-tag :type="statusType" size="small" round class="status-tag">
        {{ statusText }}
      </n-tag>
    </div>
    <div class="app-name">{{ appLabels[appName] || appName }}</div>
    <div class="app-key">{{ appName }}</div>
    <div class="actions">
      <n-button
        size="small"
        type="primary"
        :disabled="!canStart"
        @click="appStore.start(appName)"
      >
        <template #icon><n-icon :component="Play" /></template>
        启动
      </n-button>
      <n-button
        size="small"
        type="error"
        ghost
        :disabled="!isRunning"
        @click="appStore.stop(appName)"
      >
        <template #icon><n-icon :component="Stop" /></template>
        停止
      </n-button>
    </div>
  </div>
</template>

<style scoped>
.app-card {
  background: #fff;
  border: 1px solid #eef1f6;
  border-radius: 12px;
  padding: 18px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.app-card:hover {
  box-shadow: 0 8px 24px rgba(31, 41, 55, 0.08);
  transform: translateY(-2px);
}
.app-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: #d1d5db;
}
.app-card.status-running::before {
  background: #18a058;
}
.app-card.status-failed::before {
  background: #d03050;
}
.app-card.status-starting::before,
.app-card.status-stopping::before {
  background: #f0a020;
}

.card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.app-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: #f0f3ff;
  color: #4f6ef7;
  display: flex;
  align-items: center;
  justify-content: center;
}
.app-name {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-top: 14px;
}
.app-key {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 2px;
  margin-bottom: 14px;
}
.actions {
  display: flex;
  gap: 8px;
}
</style>
