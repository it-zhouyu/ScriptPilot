<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <header class="text-center mb-8">
      <h1 class="text-3xl font-bold text-gray-900 mb-2">ScriptPilot</h1>
      <p class="text-gray-500">AI 口播稿生成器 — 输入主题，自动生成口播稿</p>
    </header>

    <TopicInput :loading="loading" @generate="handleClarify" ref="topicInput" />

    <!-- Phase 1: Direction options -->
    <div v-if="phase === 'clarify'" class="mt-6">
      <div v-if="clarifyLoading" class="text-center py-12 text-gray-400">
        <span class="inline-block w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2 align-middle"></span>
        正在分析主题方向...
      </div>
      <div v-else-if="options.length" class="space-y-4">
        <p class="text-gray-600 text-sm">{{ analysis }}</p>
        <h3 class="text-lg font-semibold text-gray-800">请选择创作方向：</h3>
        <div v-for="opt in options" :key="opt.id"
          @click="handleSelectDirection(opt)"
          class="direction-card group cursor-pointer border border-gray-200 rounded-xl p-5 hover:border-blue-400 hover:shadow-md transition-all"
        >
          <div class="flex items-start gap-4">
            <span class="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center font-bold text-sm group-hover:bg-blue-600 group-hover:text-white transition-colors">{{ opt.id }}</span>
            <div class="flex-1">
              <h4 class="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{{ opt.title }}</h4>
              <p class="text-gray-500 text-sm mt-1">{{ opt.description }}</p>
              <span class="inline-block mt-2 text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded">{{ opt.audience }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Phase 2: Pipeline content -->
    <div v-if="hasStarted" class="mt-6">
      <ContentPanel :stageData="stageData" :thinkingData="thinkingData" :activeStage="currentStage" ref="contentPanel" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import TopicInput from './components/TopicInput.vue'
import ContentPanel from './components/ContentPanel.vue'
import { fetchSSE } from './api/sse.js'

const loading = ref(false)
const phase = ref('')          // '' | 'clarify' | 'generate'
const clarifyLoading = ref(false)
const analysis = ref('')
const options = ref([])
const selectedDirection = ref('')
const hasStarted = ref(false)
const currentStage = ref('')
const stageData = reactive({ research: '', outline: '', content: '', script: '' })
const thinkingData = reactive({ research: '', outline: '', content: '', script: '' })

const topicInput = ref(null)
const contentPanel = ref(null)
let currentTopic = ''

function resetState() {
  phase.value = ''
  clarifyLoading.value = false
  analysis.value = ''
  options.value = []
  selectedDirection.value = ''
  hasStarted.value = false
  currentStage.value = ''
  Object.keys(stageData).forEach(k => stageData[k] = '')
  Object.keys(thinkingData).forEach(k => thinkingData[k] = '')
}

async function handleClarify(topic) {
  resetState()
  currentTopic = topic
  phase.value = 'clarify'
  clarifyLoading.value = true

  await fetchSSE('/api/clarify', { topic }, {
    onOptions(data) {
      analysis.value = data.analysis || ''
      options.value = data.options || []
    },
    onDone() {
      clarifyLoading.value = false
    },
    onError(err) {
      console.error('Clarify error:', err)
      clarifyLoading.value = false
    },
  })
}

async function handleSelectDirection(opt) {
  selectedDirection.value = opt.title + '：' + opt.description
  phase.value = 'generate'
  loading.value = true
  hasStarted.value = true
  currentStage.value = ''
  Object.keys(stageData).forEach(k => stageData[k] = '')
  Object.keys(thinkingData).forEach(k => thinkingData[k] = '')

  if (contentPanel.value) contentPanel.value.reset()

  const directionText = `${currentTopic} — ${opt.title}（${opt.description}）`

  await fetchSSE('/api/generate', { topic: currentTopic, direction: directionText }, {
    onStage(data) {
      if (data.status === 'running') currentStage.value = data.stage
    },
    onToken(data) {
      stageData[data.stage] += data.token
    },
    onThinking(data) {
      thinkingData[data.stage] += data.token
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
