<script setup lang="ts">
// 论坛监控页：采集启停、最新/历史日志
import { computed, onMounted, ref } from 'vue'
import { NIcon } from 'naive-ui'
import {
  ChatbubblesOutline,
  Play,
  Stop,
  TimeOutline,
  ListOutline,
} from '@vicons/ionicons5'
import OutputPanel from '@/components/OutputPanel.vue'
import { useForumStore } from '@/stores/forum'

const forumStore = useForumStore()
const historyDate = ref('')

const running = computed(() => forumStore.taskStatus === 'running')

onMounted(async () => {
  await forumStore.fetchLog()
})

async function onQueryHistory() {
  if (!historyDate.value) return
  await forumStore.fetchHistory(historyDate.value)
}
</script>

<template>
  <div class="forum-page">
    <!-- 采集控制卡片 -->
    <div class="control-card">
      <div class="control-info">
        <div class="control-icon">
          <n-icon :component="ChatbubblesOutline" :size="26" />
        </div>
        <div>
          <div class="control-title">论坛采集</div>
          <div class="control-status">
            <span class="dot" :class="{ on: running }"></span>
            {{ running ? '采集中' : '已停止' }}
          </div>
        </div>
      </div>
      <n-space :size="10">
        <n-button type="primary" :disabled="running" @click="forumStore.start">
          <template #icon><n-icon :component="Play" /></template>
          启动采集
        </n-button>
        <n-button type="error" ghost :disabled="!running" @click="forumStore.stop">
          <template #icon><n-icon :component="Stop" /></template>
          停止采集
        </n-button>
      </n-space>
    </div>

    <div class="two-col">
      <!-- 最新日志 -->
      <div class="panel">
        <div class="panel-head">
          <n-icon :component="ListOutline" :size="18" color="#4f6ef7" />
          <span>最新日志</span>
        </div>
        <OutputPanel :lines="forumStore.logLines" title="论坛最新日志" />
      </div>

      <!-- 历史日志 -->
      <div class="panel">
        <div class="panel-head">
          <n-icon :component="TimeOutline" :size="18" color="#4f6ef7" />
          <span>历史日志查询</span>
        </div>
        <n-space class="history-form">
          <n-input
            v-model:value="historyDate"
            placeholder="日期，如 2026-08-26"
            style="flex: 1"
          />
          <n-button type="primary" @click="onQueryHistory">查询</n-button>
        </n-space>
        <n-data-table
          v-if="forumStore.history.length"
          :columns="[
            { title: '时间', key: 'time' },
            { title: '事件', key: 'event' },
            { title: '消息', key: 'message' },
            { title: '状态', key: 'task_status' },
          ]"
          :data="forumStore.history"
          size="small"
          style="margin-top: 16px"
        />
        <div v-else class="empty-hint">选择日期查询历史日志</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.forum-page {
  max-width: 1200px;
  margin: 0 auto;
}
.control-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: 14px;
  padding: 24px 28px;
  box-shadow: 0 2px 12px rgba(31, 41, 55, 0.05);
  margin-bottom: 20px;
}
.control-info {
  display: flex;
  align-items: center;
  gap: 14px;
}
.control-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: #f0f3ff;
  color: #4f6ef7;
  display: flex;
  align-items: center;
  justify-content: center;
}
.control-title {
  font-size: 17px;
  font-weight: 600;
  color: #1f2937;
}
.control-status {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 2px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
  display: inline-block;
}
.dot.on {
  background: #18a058;
  box-shadow: 0 0 8px #18a058;
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
}
.history-form {
  display: flex;
  gap: 10px;
}
.empty-hint {
  color: #9ca3af;
  text-align: center;
  padding: 40px 0;
  font-size: 13px;
}
@media (max-width: 900px) {
  .two-col {
    grid-template-columns: 1fr;
  }
}
</style>
