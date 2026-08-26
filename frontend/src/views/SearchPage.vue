<script setup lang="ts">
// 主题检索页：输入主题词发起检索，查看结构化报告
import { ref } from 'vue'
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
    <n-card title="主题检索" size="small">
      <n-space vertical>
        <n-input v-model:value="query" placeholder="输入主题词或关键词" />
        <n-select
          v-model:value="sourceTypes"
          multiple
          :options="sourceOptions"
          placeholder="选择来源类型"
        />
        <n-button type="primary" :loading="loading" @click="onSubmit">发起检索</n-button>
        <n-alert v-if="error" type="error" :show-icon="true">{{ error }}</n-alert>
      </n-space>
    </n-card>

    <n-card v-if="result" title="分析报告" size="small" class="result-card">
      <template #header-extra>
        <n-tag type="info">{{ result.report_id }}</n-tag>
      </template>
      <div class="report-markdown">{{ result.report_md }}</div>
    </n-card>
  </div>
</template>

<style scoped>
.search-page {
  padding: 16px;
}
.result-card {
  margin-top: 16px;
}
.report-markdown {
  white-space: pre-wrap;
  font-family: inherit;
  line-height: 1.6;
  max-height: 600px;
  overflow-y: auto;
}
</style>
