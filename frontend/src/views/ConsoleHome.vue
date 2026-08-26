<script setup lang="ts">
// 控制台首页：应用状态、启停按钮、系统状态
import { onMounted } from 'vue'
import AppStatusCard from '@/components/AppStatusCard.vue'
import { useAppStore } from '@/stores/app'
import { useSystemStore } from '@/stores/system'

const appStore = useAppStore()
const systemStore = useSystemStore()

const defaultApps = ['search', 'media', 'forum', 'insight', 'report']

onMounted(async () => {
  await appStore.fetchStatus()
  await systemStore.fetchStatus()
})
</script>

<template>
  <div class="console-home">
    <n-space vertical :size="16">
      <n-card title="系统状态" size="small">
        <n-space>
          <n-tag :type="systemStore.systemStatus === 'online' ? 'success' : 'warning'">
            系统：{{ systemStore.systemStatus }}
          </n-tag>
          <n-button size="small" type="primary" @click="systemStore.start">启动系统</n-button>
          <n-button size="small" type="error" @click="systemStore.shutdown">关闭系统</n-button>
        </n-space>
      </n-card>

      <n-card title="单功能应用" size="small">
        <n-grid :cols="3" :x-gap="12" :y-gap="12">
          <n-grid-item v-for="name in defaultApps" :key="name">
            <AppStatusCard :app-name="name" />
          </n-grid-item>
        </n-grid>
      </n-card>
    </n-space>
  </div>
</template>

<style scoped>
.console-home {
  padding: 16px;
}
</style>
