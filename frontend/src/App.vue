<script setup lang="ts">
// 根组件：Naive UI Provider + 布局 + 全局 WebSocket 分发
import { NConfigProvider, NLayout, NLayoutHeader, NLayoutSider, NLayoutContent, NMenu } from 'naive-ui'
import { computed, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAppStore } from '@/stores/app'
import { useSystemStore } from '@/stores/system'
import { useForumStore } from '@/stores/forum'
import { useGraphStore } from '@/stores/graph'
import type { WsMessage } from '@/types'

const route = useRoute()
const router = useRouter()

const appStore = useAppStore()
const systemStore = useSystemStore()
const forumStore = useForumStore()
const graphStore = useGraphStore()

// WebSocket 地址：开发经 vite 代理，生产同源
const wsUrl = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`
const { connected, connect, disconnect, onMessage } = useWebSocket(wsUrl)

// 消息分发到对应 Store
onMessage((msg: WsMessage) => {
  const d = msg.data
  switch (msg.type) {
    case 'app_status':
      appStore.handleStatus(d.app_name as string, d.status as string)
      break
    case 'app_output':
      appStore.handleOutput(d.app_name as string, d.output_text as string)
      break
    case 'forum_log':
      forumStore.handleLog(d.message_text as string, d.task_status as string)
      break
    case 'system_status':
      systemStore.handleSystemStatus(
        d.system_status as string,
        (d.running_apps as string[]) || [],
      )
      break
    case 'graph_ready':
      graphStore.handleGraphReady(d.report_id as string)
      break
    case 'error':
      systemStore.handleError(d.module_name as string, d.error_message as string)
      break
  }
})

onMounted(() => connect())
onBeforeUnmount(() => disconnect())

const menuOptions = [
  { label: '控制台', key: '/' },
  { label: '主题检索', key: '/search' },
  { label: '论坛监控', key: '/forum' },
  { label: '图谱查看', key: '/graph-viewer' },
  { label: '配置管理', key: '/config' },
  { label: '系统状态', key: '/system' },
]

const activeKey = computed(() => route.path)
function onMenuSelect(key: string) {
  router.push(key)
}
</script>

<template>
  <n-config-provider>
    <n-layout has-sider style="height: 100vh">
      <n-layout-sider bordered width="200">
        <div class="logo">舆情分析平台</div>
        <n-menu
          :options="menuOptions"
          :value="activeKey"
          @update:value="onMenuSelect"
        />
      </n-layout-sider>
      <n-layout>
        <n-layout-header bordered class="header">
          <n-space align="center">
            <n-tag :type="connected ? 'success' : 'error'" size="small">
              {{ connected ? '已连接' : '未连接' }}
            </n-tag>
          </n-space>
        </n-layout-header>
        <n-layout-content>
          <router-view />
        </n-layout-content>
      </n-layout>
    </n-layout>
  </n-config-provider>
</template>

<style>
html,
body,
#app {
  margin: 0;
  height: 100%;
}
.logo {
  padding: 16px;
  font-weight: 600;
  font-size: 16px;
  color: #2080f0;
  border-bottom: 1px solid #eee;
}
.header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
}
</style>
