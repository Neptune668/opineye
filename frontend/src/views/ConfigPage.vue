<script setup lang="ts">
// 配置管理页：配置读取、编辑、保存
import { onMounted, ref } from 'vue'
import { getConfig, updateConfig } from '@/api'

const configText = ref('')
const message = ref('')
const error = ref('')

onMounted(async () => {
  try {
    const data = await getConfig()
    configText.value = JSON.stringify(data.config, null, 2)
  } catch (e) {
    error.value = (e as Error).message
  }
})

async function onSave() {
  try {
    const config = JSON.parse(configText.value)
    await updateConfig(config)
    message.value = '配置已保存并生效'
    error.value = ''
  } catch (e) {
    error.value = (e as Error).message
    message.value = ''
  }
}
</script>

<template>
  <div class="config-page">
    <n-card title="系统配置" size="small">
      <n-space vertical>
        <n-input
          v-model:value="configText"
          type="textarea"
          :rows="18"
          :autosize="{ minRows: 12, maxRows: 24 }"
          placeholder="配置 JSON"
        />
        <n-space>
          <n-button type="primary" @click="onSave">保存配置</n-button>
          <n-tag v-if="message" type="success">{{ message }}</n-tag>
          <n-tag v-if="error" type="error">{{ error }}</n-tag>
        </n-space>
      </n-space>
    </n-card>
  </div>
</template>

<style scoped>
.config-page {
  padding: 16px;
}
</style>
