<script setup lang="ts">
// 论坛监控页：采集启停、最新/历史日志
import { onMounted, ref } from 'vue'
import OutputPanel from '@/components/OutputPanel.vue'
import { useForumStore } from '@/stores/forum'

const forumStore = useForumStore()
const historyDate = ref('')

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
    <n-space vertical :size="16">
      <n-card title="论坛采集" size="small">
        <n-space>
          <n-tag :type="forumStore.taskStatus === 'running' ? 'success' : 'default'">
            状态：{{ forumStore.taskStatus }}
          </n-tag>
          <n-button size="small" type="primary" @click="forumStore.start">启动采集</n-button>
          <n-button size="small" type="error" @click="forumStore.stop">停止采集</n-button>
        </n-space>
      </n-card>

      <n-card title="最新日志" size="small">
        <OutputPanel :lines="forumStore.logLines" title="论坛最新日志" />
      </n-card>

      <n-card title="历史日志查询" size="small">
        <n-space>
          <n-input v-model:value="historyDate" placeholder="日期，如 2026-08-26" style="width: 200px" />
          <n-button size="small" type="primary" @click="onQueryHistory">查询</n-button>
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
          style="margin-top: 12px"
        />
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.forum-page {
  padding: 16px;
}
</style>
