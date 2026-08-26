<script setup lang="ts">
// 输出查看面板：滚动展示应用输出（自动跟随底部）
import { nextTick, ref, watch } from 'vue'

const props = defineProps<{ lines: string[]; title?: string }>()
const container = ref<HTMLElement | null>(null)

watch(
  () => props.lines.length,
  async () => {
    await nextTick()
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  },
)
</script>

<template>
  <div class="output-panel">
    <div class="output-header">
      <span class="header-title">{{ title || '输出' }}</span>
      <span class="header-count">{{ lines.length }} 行</span>
    </div>
    <div ref="container" class="output-body">
      <pre v-if="lines.length">{{ lines.join('\n') }}</pre>
      <div v-else class="empty">
        <span class="empty-icon">⌁</span>
        <span>暂无输出</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.output-panel {
  border: 1px solid #eef1f6;
  border-radius: 10px;
  overflow: hidden;
}
.output-header {
  padding: 10px 14px;
  background: #fafbfc;
  border-bottom: 1px solid #eef1f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-title {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
}
.header-count {
  font-size: 12px;
  color: #9ca3af;
}
.output-body {
  height: 300px;
  overflow-y: auto;
  padding: 14px;
  background: #1a1d27;
}
.output-body pre {
  margin: 0;
  color: #d4d4d4;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-all;
}
.empty {
  color: #6b7280;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  font-size: 13px;
}
.empty-icon {
  font-size: 24px;
  opacity: 0.5;
}
</style>
