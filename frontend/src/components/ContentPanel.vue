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
        <div v-if="thinkingOpen" class="thinking-content bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-900 leading-relaxed max-h-[200px] overflow-y-auto">{{ activeThinking }}</div>
      </div>

      <!-- Content rendered as HTML -->
      <div v-if="!activeContent" class="text-gray-400 text-center py-12">
        {{ activeStage === activeTab ? '正在生成...' : '等待生成...' }}
      </div>
      <div v-else class="prose-content" v-html="activeContent"></div>
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

<style>
.prose-content {
  color: #334155;
  font-size: 15px;
  line-height: 1.85;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
}
.prose-content h1 {
  font-size: 1.6em;
  font-weight: 700;
  margin: 1.2em 0 0.6em;
  color: #0f172a;
  letter-spacing: -0.02em;
}
.prose-content h2 {
  font-size: 1.35em;
  font-weight: 600;
  margin: 1.4em 0 0.8em;
  color: #1e293b;
  padding-bottom: 0.4em;
  border-bottom: 2px solid #e2e8f0;
  position: relative;
}
.prose-content h2::after {
  content: "";
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
}
.prose-content h3 {
  font-size: 1.15em;
  font-weight: 600;
  margin: 1em 0 0.4em;
  color: #334155;
  padding-left: 0.6em;
  border-left: 3px solid #3b82f6;
}
.prose-content p {
  margin: 0.8em 0;
  text-align: justify;
}
.prose-content ul, .prose-content ol {
  margin: 0.8em 0;
  padding-left: 1.6em;
}
.prose-content li {
  margin: 0.35em 0;
  line-height: 1.75;
}
.prose-content ul li {
  list-style: none;
  position: relative;
  padding-left: 0.4em;
}
.prose-content ul li::before {
  content: "";
  position: absolute;
  left: -1em;
  top: 0.65em;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #3b82f6;
}
.prose-content ol li {
  list-style: none;
  counter-increment: item;
  position: relative;
  padding-left: 0.4em;
}
.prose-content ol li::before {
  content: counter(item);
  position: absolute;
  left: -1.6em;
  top: 0.1em;
  width: 1.2em;
  height: 1.2em;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  font-size: 0.7em;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}
.prose-content strong {
  font-weight: 600;
  color: #0f172a;
  background: linear-gradient(180deg, transparent 60%, #bfdbfe 60%);
  padding: 0 0.1em;
}
.prose-content em {
  font-style: normal;
  color: #6366f1;
  background: #eef2ff;
  padding: 0.1em 0.3em;
  border-radius: 3px;
  font-size: 0.9em;
}
.prose-content blockquote {
  border-left: 4px solid #3b82f6;
  padding: 0.8em 1em;
  margin: 1em 0;
  background: #eff6ff;
  border-radius: 0 6px 6px 0;
  color: #1e40af;
  font-size: 0.95em;
}
.prose-content blockquote p {
  margin: 0.3em 0;
}
.prose-content code {
  background: #f1f5f9;
  color: #e11d48;
  padding: 0.15em 0.45em;
  border-radius: 4px;
  font-size: 0.88em;
  font-family: "JetBrains Mono", "Fira Code", monospace;
}
.prose-content pre {
  background: #0f172a;
  color: #e2e8f0;
  padding: 1.2em;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1em 0;
  font-size: 0.88em;
  line-height: 1.6;
  border: 1px solid #1e293b;
}
.prose-content pre code {
  background: none;
  color: inherit;
  padding: 0;
}
.prose-content hr {
  border: none;
  height: 2px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #3b82f6);
  margin: 2em 0;
  border-radius: 1px;
}
.prose-content table {
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
  margin: 1em 0;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}
.prose-content th {
  background: linear-gradient(180deg, #f8fafc, #f1f5f9);
  font-weight: 600;
  color: #334155;
  padding: 0.7em 1em;
  text-align: left;
  font-size: 0.9em;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;
}
.prose-content td {
  padding: 0.6em 1em;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}
.prose-content tr:last-child td {
  border-bottom: none;
}
.prose-content tr:hover td {
  background: #f8fafc;
}

/* Search result cards */
.search-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 1em 1.2em;
  margin: 0.8em 0;
  transition: box-shadow 0.2s;
}
.search-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.search-card-header {
  display: flex;
  align-items: center;
  gap: 0.6em;
  margin-bottom: 0.5em;
}
.search-card-index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.6em;
  height: 1.6em;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: white;
  border-radius: 50%;
  font-size: 0.75em;
  font-weight: 700;
  flex-shrink: 0;
}
.search-card-title {
  font-weight: 600;
  font-size: 1em;
  color: #1e293b;
  line-height: 1.4;
}
.search-card-content {
  color: #475569;
  font-size: 0.92em;
  line-height: 1.7;
  margin: 0.4em 0;
}
.search-card-url {
  display: inline-block;
  font-size: 0.8em;
  color: #6366f1;
  text-decoration: none;
  padding: 0.15em 0;
  border-bottom: 1px dashed #c7d2fe;
  transition: color 0.2s;
}
.search-card-url:hover {
  color: #4338ca;
}
</style>
