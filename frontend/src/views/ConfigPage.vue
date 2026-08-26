<script setup lang="ts">
// 配置管理页：配置读取、编辑、保存
import { onMounted, ref } from 'vue'
import { NIcon } from 'naive-ui'
import { SettingsOutline, SaveOutline, CheckmarkCircleOutline, AlertCircleOutline } from '@vicons/ionicons5'
import { getConfig, updateConfig } from '@/api'

const configText = ref('')
const message = ref('')
const error = ref('')
const saving = ref(false)

onMounted(async () => {
  try {
    const data = await getConfig()
    configText.value = JSON.stringify(data.config, null, 2)
  } catch (e) {
    error.value = (e as Error).message
  }
})

async function onSave() {
  saving.value = true
  try {
    const config = JSON.parse(configText.value)
    await updateConfig(config)
    message.value = '配置已保存并生效'
    error.value = ''
  } catch (e) {
    error.value = (e as Error).message
    message.value = ''
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="config-page">
    <div class="panel">
      <div class="panel-head">
        <div class="head-left">
          <n-icon :component="SettingsOutline" :size="20" color="#4f6ef7" />
          <span>系统配置</span>
        </div>
        <span class="head-sub">修改后保存即时生效，自动备份 config.json.bak</span>
      </div>

      <n-input
        v-model:value="configText"
        type="textarea"
        :autosize="{ minRows: 18, maxRows: 30 }"
        placeholder="配置 JSON"
        class="config-editor"
      />

      <div class="footer">
        <n-button type="primary" :loading="saving" @click="onSave">
          <template #icon><n-icon :component="SaveOutline" /></template>
          保存配置
        </n-button>
        <div v-if="message" class="msg success">
          <n-icon :component="CheckmarkCircleOutline" />
          {{ message }}
        </div>
        <div v-if="error" class="msg error">
          <n-icon :component="AlertCircleOutline" />
          {{ error }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.config-page {
  max-width: 960px;
  margin: 0 auto;
}
.panel {
  background: #fff;
  border-radius: 14px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(31, 41, 55, 0.05);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #f0f2f5;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}
.head-sub {
  font-size: 12px;
  color: #9ca3af;
}
.config-editor {
  font-family: 'Consolas', 'Monaco', monospace;
}
.footer {
  margin-top: 18px;
  display: flex;
  align-items: center;
  gap: 14px;
}
.msg {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.msg.success {
  color: #18a058;
}
.msg.error {
  color: #d03050;
}
</style>
