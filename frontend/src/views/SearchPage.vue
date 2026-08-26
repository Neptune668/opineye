<script setup lang="ts">
// 主题检索页：输入主题词发起检索，查看结构化报告
import { ref } from 'vue'
import { NIcon } from 'naive-ui'
import { SearchOutline, DocumentTextOutline } from '@vicons/ionicons5'
import { search } from '@/api'
import type { SearchResult } from '@/types'

const query = ref('')
const sourceTypes = ref(['news', 'forum_post', 'internal_data'])
const loading = ref(false)
const result = ref<SearchResult | null>(null)
const error = ref('')

const sourceOptions = [
  { label: '新闻', value: 'news' },
  { label: '图片', value: 'image' },
  { label: '视频', value: 'video' },
  { label: '论坛帖子', value: 'forum_post' },
  { label: '内部数据', value: 'internal_data' },
]

async function onSubmit() {
  if (!query.value.trim()) {
    error.value = '请输入主题词'
    return
  }
  loading.value = true
  error.value = ''
  try {
    result.value = await search({
      query: query.value.trim(),
      source_types: sourceTypes.value,
    })
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="search-page">
    <div class="search-card">
      <div class="search-head">
        <n-icon :component="SearchOutline" :size="24" color="#4f6ef7" />
        <div>
          <div class="search-title">主题检索</div>
          <div class="search-sub">输入主题词，从多来源并行采集并生成结构化舆情报告</div>
        </div>
      </div>
      <div class="search-form">
        <n-input
          v-model:value="query"
          size="large"
          placeholder="输入主题词或关键词，例如：MCP 协议发布"
          @keyup.enter="onSubmit"
        />
        <div class="source-label">来源类型</div>
        <n-select
          v-model:value="sourceTypes"
          multiple
          size="large"
          :options="sourceOptions"
          placeholder="选择来源类型"
        />
        <n-button
          type="primary"
          size="large"
          :loading="loading"
          block
          @click="onSubmit"
        >
          <template #icon><n-icon :component="SearchOutline" /></template>
          发起检索
        </n-button>
        <n-alert v-if="error" type="error" :show-icon="true">{{ error }}</n-alert>
      </div>
    </div>

    <div v-if="result" class="result-card">
      <div class="result-head">
        <div class="result-title">
          <n-icon :component="DocumentTextOutline" :size="20" color="#4f6ef7" />
          <span>分析报告</span>
        </div>
        <n-tag type="info" round>{{ result.report_id }}</n-tag>
      </div>
      <div class="report-markdown">{{ result.report_md }}</div>
    </div>
  </div>
</template>

<style scoped>
.search-page {
  max-width: 960px;
  margin: 0 auto;
}
.search-card {
  background: #fff;
  border-radius: 14px;
  padding: 28px;
  box-shadow: 0 2px 12px rgba(31, 41, 55, 0.05);
}
.search-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}
.search-title {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}
.search-sub {
  font-size: 13px;
  color: #9ca3af;
  margin-top: 2px;
}
.search-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.source-label {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
}
.result-card {
  background: #fff;
  border-radius: 14px;
  padding: 28px;
  margin-top: 20px;
  box-shadow: 0 2px 12px rgba(31, 41, 55, 0.05);
}
.result-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f0f2f5;
}
.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}
.report-markdown {
  white-space: pre-wrap;
  font-family: inherit;
  line-height: 1.7;
  max-height: 640px;
  overflow-y: auto;
  color: #374151;
}
</style>
