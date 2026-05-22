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
      <div v-if="!tabs.find(t => t.key === activeTab)?.content" class="text-gray-400 text-center py-12">
        {{ activeStage === activeTab ? '正在生成...' : '等待生成...' }}
      </div>
      <pre v-else class="whitespace-pre-wrap text-gray-800 text-sm leading-relaxed font-sans">{{ tabs.find(t => t.key === activeTab)?.content }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  stageData: { type: Object, required: true },
  activeStage: { type: String, default: '' },
})

const activeTab = ref('research')

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

watch(() => props.activeStage, (stage) => {
  if (stage) activeTab.value = stage
})

function reset() {
  activeTab.value = 'research'
}

defineExpose({ reset })
</script>
