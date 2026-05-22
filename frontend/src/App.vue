<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <header class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">ScriptPilot</h1>
      <p class="text-gray-500">AI 口播稿生成器 — 输入主题，自动生成口播稿</p>
    </header>

    <TopicInput :loading="loading" @generate="handleGenerate" ref="topicInput" />

    <div v-if="hasStarted" class="mt-6">
      <ContentPanel :stageData="stageData" :activeStage="currentStage" ref="contentPanel" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import TopicInput from './components/TopicInput.vue'
import ContentPanel from './components/ContentPanel.vue'
import { fetchSSE } from './api/sse.js'

const loading = ref(false)
const hasStarted = ref(false)
const currentStage = ref('')
const stageData = reactive({
  research: '',
  outline: '',
  content: '',
  script: '',
})

const topicInput = ref(null)
const contentPanel = ref(null)

async function handleGenerate(topic) {
  loading.value = true
  hasStarted.value = true
  currentStage.value = ''
  Object.keys(stageData).forEach(k => stageData[k] = '')

  if (contentPanel.value) contentPanel.value.reset()

  await fetchSSE('/api/generate', { topic }, {
    onStage(data) {
      if (data.status === 'running') {
        currentStage.value = data.stage
      }
    },
    onToken(data) {
      stageData[data.stage] += data.token
    },
    onDone() {
      loading.value = false
      currentStage.value = ''
    },
    onError(err) {
      console.error('SSE error:', err)
      loading.value = false
    },
  })
}
</script>
