<template>
  <div class="bg-white rounded-lg shadow-sm border border-gray-200">
    <div class="flex border-b border-gray-200">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        :class="[
          'px-5 py-3 text-sm font-medium border-b-2 transition-colors',
          activeTab === tab.key
            ? 'border-blue-600 text-blue-600 bg-blue-50'
            : 'border-transparent text-gray-500 hover:text-gray-700',
          tab.completed ? 'text-green-600' : '',
        ]"
      >
        <span v-if="tab.completed" class="mr-1">&#10003;</span>
        {{ tab.label }}
      </button>
    </div>
    <div class="p-6 min-h-[400px] max-h-[600px] overflow-y-auto">
      <!-- Thinking section (collapsible) -->
      <div v-if="activeThinking" class="mb-4">
        <button @click="thinkingOpen = !thinkingOpen" class="flex items-center gap-1 text-sm text-amber-600 hover:text-amber-700 font-medium mb-2">
          <span :class="thinkingOpen ? 'rotate-90' : ''" class="transition-transform inline-block">&#9654;</span>
          AI 思考过程
        </button>
        <div v-if="thinkingOpen" class="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900 leading-relaxed whitespace-pre-wrap font-sans max-h-[200px] overflow-y-auto">{{ activeThinking }}</div>
      </div>

      <!-- Content -->
      <div v-if="!activeContent" class="text-gray-400 text-center py-12">
        {{ activeStage === activeTab ? '正在生成...' : '等待生成...' }}
      </div>
      <pre v-else class="whitespace-pre-wrap text-gray-800 text-sm leading-relaxed font-sans">{{ activeContent }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  stageData: { type: Object, required: true },
  thinkingData: { type: Object, default: () => ({}) },
  activeStage: { type: String, default: '' },
})

const activeTab = ref('research')
const thinkingOpen = ref(true)

const STAGES = [
  { key: 'research', label: '资料收集' },
  { key: 'outline', label: '文章大纲' },
  { key: 'content', label: '正文内容' },
  { key: 'script', label: '口播稿' },
]

const tabs = computed(() =>
  STAGES.map(s => ({
    key: s.key,
    label: s.label,
    content: props.stageData[s.key] || '',
    completed: !!props.stageData[s.key] && props.activeStage !== s.key,
  }))
)

const activeContent = computed(() => props.stageData[activeTab.value] || '')
const activeThinking = computed(() => props.thinkingData[activeTab.value] || '')

watch(() => props.activeStage, (stage) => {
  if (stage) activeTab.value = stage
})

function reset() {
  activeTab.value = 'research'
  thinkingOpen.value = true
}

defineExpose({ reset })
</script>
