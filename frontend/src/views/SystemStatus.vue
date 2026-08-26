<script setup lang="ts">
// 系统状态页：整体服务状态、各应用状态、最近错误
import { computed, onMounted } from 'vue'
import { NIcon, NTag } from 'naive-ui'
import {
  ServerOutline,
  AppsOutline,
  AlertCircleOutline,
  CheckmarkCircleOutline,
} from '@vicons/ionicons5'
import { useAppStore } from '@/stores/app'
import { useSystemStore } from '@/stores/system'

const appStore = useAppStore()
const systemStore = useSystemStore()

const appRows = computed(() =>
  Object.entries(appStore.apps).map(([name, status]) => ({ name, status })),
)

const statusType = (s: string) => {
  const map: Record<string, any> = {
    running: 'success',
    failed: 'error',
    starting: 'warning',
    stopping: 'warning',
    stopped: 'default',
  }
  return map[s] || 'default'
}

const statusText = (s: string) => {
  const map: Record<string, string> = {
    stopped: '已停止',
    starting: '启动中',
    running: '运行中',
    stopping: '停止中',
    failed: '异常',
  }
  return map[s] || s
}

onMounted(async () => {
  await appStore.fetchStatus()
  await systemStore.fetchStatus()
})
</script>

<template>
  <div class="system-status">
    <!-- 概览卡片 -->
    <div class="overview">
      <div class="ov-card">
        <div class="ov-icon purple">
          <n-icon :component="ServerOutline" :size="24" />
        </div>
        <div>
          <div class="ov-label">系统状态</div>
          <div class="ov-value">{{ systemStore.systemStatus }}</div>
        </div>
      </div>
      <div class="ov-card">
        <div class="ov-icon blue">
          <n-icon :component="AppsOutline" :size="24" />
        </div>
        <div>
          <div class="ov-label">运行中应用</div>
          <div class="ov-value">{{ Object.keys(systemStore.runningApps).length }}</div>
        </div>
      </div>
      <div class="ov-card">
        <div class="ov-icon red">
          <n-icon :component="AlertCircleOutline" :size="24" />
        </div>
        <div>
          <div class="ov-label">错误数</div>
          <div class="ov-value">{{ systemStore.errors.length }}</div>
        </div>
      </div>
    </div>

    <div class="two-col">
      <!-- 应用状态 -->
      <div class="panel">
        <div class="panel-head">
          <n-icon :component="AppsOutline" :size="18" color="#4f6ef7" />
          <span>应用状态</span>
        </div>
        <div v-if="appRows.length" class="app-list">
          <div v-for="row in appRows" :key="row.name" class="app-row">
            <span class="app-name">{{ row.name }}</span>
            <n-tag :type="statusType(row.status)" size="small" round>
              {{ statusText(row.status) }}
            </n-tag>
          </div>
        </div>
        <div v-else class="empty-hint">暂无应用数据</div>
      </div>

      <!-- 最近错误 -->
      <div class="panel">
        <div class="panel-head">
          <n-icon :component="AlertCircleOutline" :size="18" color="#d03050" />
          <span>最近错误</span>
        </div>
        <div v-if="!systemStore.errors.length" class="no-error">
          <n-icon :component="CheckmarkCircleOutline" :size="32" color="#18a058" />
          <span>暂无错误</span>
        </div>
        <div v-else class="error-list">
          <n-alert
            v-for="(err, i) in systemStore.errors"
            :key="i"
            type="error"
            :show-icon="true"
            class="error-item"
          >
            {{ err }}
          </n-alert>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.system-status {
  max-width: 1200px;
  margin: 0 auto;
}
.overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.ov-card {
  background: #fff;
  border-radius: 14px;
  padding: 20px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(31, 41, 55, 0.05);
}
.ov-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.ov-icon.purple {
  background: #f0f3ff;
  color: #4f6ef7;
}
.ov-icon.blue {
  background: #e8f4fd;
  color: #2080f0;
}
.ov-icon.red {
  background: #fdeaea;
  color: #d03050;
}
.ov-label {
  font-size: 13px;
  color: #9ca3af;
}
.ov-value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin-top: 2px;
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
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
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f2f5;
}
.app-list {
  display: flex;
  flex-direction: column;
}
.app-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 4px;
  border-bottom: 1px solid #f7f8fa;
}
.app-row:last-child {
  border-bottom: none;
}
.app-name {
  font-size: 14px;
  color: #374151;
  font-weight: 500;
}
.empty-hint {
  color: #9ca3af;
  text-align: center;
  padding: 40px 0;
  font-size: 13px;
}
.no-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 0;
  color: #9ca3af;
  font-size: 13px;
}
.error-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
@media (max-width: 900px) {
  .overview,
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
