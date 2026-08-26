<script setup lang="ts">
// 系统状态页：整体服务状态、各应用状态、最近错误
import { onMounted } from 'vue'
import { useAppStore } from '@/stores/app'
import { useSystemStore } from '@/stores/system'

const appStore = useAppStore()
const systemStore = useSystemStore()

onMounted(async () => {
  await appStore.fetchStatus()
  await systemStore.fetchStatus()
})
</script>

<template>
  <div class="system-status">
    <n-space vertical :size="16">
      <n-card title="整体服务" size="small">
        <n-descriptions bordered :column="2" size="small">
          <n-descriptions-item label="系统状态">
            {{ systemStore.systemStatus }}
          </n-descriptions-item>
          <n-descriptions-item label="运行中应用数">
            {{ Object.keys(systemStore.runningApps).length }}
          </n-descriptions-item>
        </n-descriptions>
      </n-card>

      <n-card title="应用状态" size="small">
        <n-data-table
          :columns="[
            { title: '应用', key: 'name' },
            { title: '状态', key: 'status' },
          ]"
          :data="Object.entries(appStore.apps).map(([name, status]) => ({ name, status }))"
          size="small"
        />
      </n-card>

      <n-card title="最近错误" size="small">
        <n-alert v-if="!systemStore.errors.length" type="success">暂无错误</n-alert>
        <div v-else>
          <n-alert
            v-for="(err, i) in systemStore.errors"
            :key="i"
            type="error"
            style="margin-bottom: 8px"
          >
            {{ err }}
          </n-alert>
        </div>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.system-status {
  padding: 16px;
}
</style>
