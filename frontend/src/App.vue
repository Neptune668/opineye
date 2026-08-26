<script setup lang="ts">
// 根组件：Naive UI Provider + 布局 + 全局 WebSocket 分发
import {
  NConfigProvider,
  NLayout,
  NLayoutHeader,
  NLayoutSider,
  NLayoutContent,
  NMenu,
  NIcon,
  type GlobalThemeOverrides,
} from 'naive-ui'
import { computed, h, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  HomeOutline,
  SearchOutline,
  ChatbubblesOutline,
  GitNetworkOutline,
  SettingsOutline,
  ServerOutline,
  RadioButtonOn,
  RadioButtonOff,
} from '@vicons/ionicons5'
import { useWebSocket } from '@/composables/useWebSocket'
import { useAppStore } from '@/stores/app'
import { useSystemStore } from '@/stores/system'
import { useForumStore } from '@/stores/forum'
import { useGraphStore } from '@/stores/graph'
import type { WsMessage } from '@/types'

// 主题色覆盖
const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#4f6ef7',
    primaryColorHover: '#6a84f9',
    primaryColorPressed: '#3c57d9',
    primaryColorSuppl: '#6a84f9',
    borderRadius: '8px',
  },
}

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

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) })
}

const menuOptions = [
  { label: '控制台', key: '/', icon: renderIcon(HomeOutline) },
  { label: '主题检索', key: '/search', icon: renderIcon(SearchOutline) },
  { label: '论坛监控', key: '/forum', icon: renderIcon(ChatbubblesOutline) },
  { label: '图谱查看', key: '/graph-viewer', icon: renderIcon(GitNetworkOutline) },
  { label: '配置管理', key: '/config', icon: renderIcon(SettingsOutline) },
  { label: '系统状态', key: '/system', icon: renderIcon(ServerOutline) },
]

const activeKey = computed(() => {
  // 图谱查看页的子路由也高亮图谱菜单
  if (route.path.startsWith('/graph-viewer')) return '/graph-viewer'
  return route.path
})

const pageTitle = computed(() => {
  const item = menuOptions.find((m) => m.key === activeKey.value)
  return item?.label || '舆情分析平台'
})

function onMenuSelect(key: string) {
  router.push(key)
}
</script>

<template>
  <n-config-provider :theme-overrides="themeOverrides">
    <n-layout has-sider style="height: 100vh">
      <n-layout-sider
        bordered
        :width="220"
        :native-scrollbar="false"
        class="sider"
      >
        <div class="logo">
          <div class="logo-icon">舆</div>
          <div class="logo-text">
            <div class="logo-title">舆情分析平台</div>
            <div class="logo-sub">Sentiment Platform</div>
          </div>
        </div>
        <n-menu
          :options="menuOptions"
          :value="activeKey"
          @update:value="onMenuSelect"
        />
      </n-layout-sider>

      <n-layout>
        <n-layout-header bordered class="header">
          <div class="header-title">{{ pageTitle }}</div>
          <n-space align="center" :size="12">
            <n-tag
              :type="connected ? 'success' : 'error'"
              size="small"
              round
              class="conn-tag"
            >
              <template #icon>
                <n-icon :component="connected ? RadioButtonOn : RadioButtonOff" />
              </template>
              {{ connected ? '实时已连接' : '连接已断开' }}
            </n-tag>
          </n-space>
        </n-layout-header>
        <n-layout-content class="content">
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC',
    'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  background: #f4f6fb;
}

/* 侧边栏 */
.sider {
  background: linear-gradient(180deg, #1e2a4a 0%, #16203a 100%) !important;
}
.sider :deep(.n-menu) {
  background: transparent;
}
.sider :deep(.n-menu .n-menu-item) {
  color: rgba(255, 255, 255, 0.7);
}
.sider :deep(.n-menu .n-menu-item:hover) {
  color: #fff;
}
.sider :deep(.n-menu .n-menu-item.n-menu-item--selected) {
  color: #fff;
  background: rgba(79, 110, 247, 0.24);
  border-radius: 8px;
}
.sider :deep(.n-menu .n-menu-item.n-menu-item--selected::before) {
  background: #4f6ef7;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 12px;
}
.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4f6ef7, #7b5cf0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
}
.logo-title {
  color: #fff;
  font-weight: 600;
  font-size: 15px;
  line-height: 1.2;
}
.logo-sub {
  color: rgba(255, 255, 255, 0.45);
  font-size: 11px;
  margin-top: 2px;
}

/* 顶栏 */
.header {
  padding: 0 24px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.header-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

/* 内容区 */
.content {
  padding: 20px;
  background: #f4f6fb;
}
</style>
