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
    <div class="output-header">{{ title || '输出' }}</div>
    <div ref="container" class="output-body">
      <pre v-if="lines.length">{{ lines.join('\n') }}</pre>
      <div v-else class="empty">暂无输出</div>
    </div>
  </div>
</template>

<style scoped>
.output-panel {
  border: 1px solid #e5e5e5;
  border-radius: 4px;
  overflow: hidden;
}
.output-header {
  padding: 8px 12px;
  background: #f7f7f7;
  font-weight: 500;
  border-bottom: 1px solid #e5e5e5;
}
.output-body {
  height: 240px;
  overflow-y: auto;
  padding: 12px;
  background: #1e1e1e;
}
.output-body pre {
  margin: 0;
  color: #d4d4d4;
  font-family: monospace;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
.empty {
  color: #888;
  text-align: center;
  padding: 20px 0;
}
</style>
