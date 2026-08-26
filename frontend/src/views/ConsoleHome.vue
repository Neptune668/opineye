<script setup lang="ts">
// 控制台首页：应用状态、启停按钮、系统状态
import { computed, onMounted } from 'vue'
import { NIcon } from 'naive-ui'
import { Play, Power, ServerOutline, AppsOutline } from '@vicons/ionicons5'
import AppStatusCard from '@/components/AppStatusCard.vue'
import { useAppStore } from '@/stores/app'
import { useSystemStore } from '@/stores/system'

const appStore = useAppStore()
const systemStore = useSystemStore()

const defaultApps = ['search', 'media', 'forum', 'insight', 'report']

const runningCount = computed(
  () => Object.values(appStore.apps).filter((s) => s === 'running').length,
)
const systemOnline = computed(() => systemStore.systemStatus === 'online')

onMounted(async () => {
  await appStore.fetchStatus()
  await systemStore.fetchStatus()
})
</script>

<template>
  <div class="console-home">
    <!-- 系统状态横幅 -->
    <div class="banner">
      <div class="banner-info">
        <div class="banner-icon">
          <n-icon :component="ServerOutline" :size="26" />
        </div>
        <div>
          <div class="banner-title">系统运行状态</div>
          <div class="banner-sub">
            <span class="dot" :class="{ on: systemOnline }"></span>
            {{ systemOnline ? '服务正常运行中' : '服务未运行' }}
            <span class="sep">·</span>
            运行中应用 {{ runningCount }}/{{ defaultApps.length }}
          </div>
        </div>
      </div>
      <n-space :size="10">
        <n-button type="primary" @click="systemStore.start">
          <template #icon><n-icon :component="Play" /></template>
          启动系统
        </n-button>
        <n-button type="error" ghost @click="systemStore.shutdown">
          <template #icon><n-icon :component="Power" /></template>
          关闭系统
        </n-button>
      </n-space>
    </div>

    <!-- 应用列表 -->
    <div class="section-header">
      <n-icon :component="AppsOutline" :size="18" color="#4f6ef7" />
      <span>单功能应用</span>
    </div>
    <n-grid :cols="3" :x-gap="16" :y-gap="16" responsive="screen">
      <n-grid-item v-for="name in defaultApps" :key="name">
        <AppStatusCard :app-name="name" />
      </n-grid-item>
    </n-grid>
  </div>
</template>

<style scoped>
.console-home {
  max-width: 1200px;
  margin: 0 auto;
}
.banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #4f6ef7 0%, #7b5cf0 100%);
  border-radius: 14px;
  padding: 24px 28px;
  color: #fff;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(79, 110, 247, 0.25);
}
.banner-info {
  display: flex;
  align-items: center;
  gap: 16px;
}
.banner-icon {
  width: 52px;
  height: 52px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}
.banner-title {
  font-size: 18px;
  font-weight: 600;
}
.banner-sub {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fca5a5;
  display: inline-block;
}
.dot.on {
  background: #4ade80;
  box-shadow: 0 0 8px #4ade80;
}
.sep {
  opacity: 0.5;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 16px;
}
</style>
