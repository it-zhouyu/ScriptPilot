<script setup>
import { ref, reactive, computed, nextTick, watch } from 'vue'
import TopicInput from './components/TopicInput.vue'
import MarkdownSplitPanel from './components/MarkdownSplitPanel.vue'
import ThinkingIndicator from './components/ThinkingIndicator.vue'
import { fetchSSE } from './api/sse.js'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const phase = ref('input')

const topic = ref('')
const analyzeThinking = ref('')
const analysis = ref('')
const options = ref([])
const selectedDirection = ref(null)
const currentStage = ref(null)
const activeView = ref('direction')
const userNavigated = ref(false)
const errorMessage = ref('')
const pendingDirection = ref(null)
const customDirection = ref('')
const isCustomDirection = ref(false)

const styleOptions = ref([])
const selectedStyle = ref(null)
const pendingStyle = ref(null)
const customStyle = ref('')
const isCustomStyle = ref(false)
const styleThinking = ref('')
const styleContent = ref('')

const clarifyContent = ref('')

const researchEnabled = ref(true)
const contentEnabled = ref(true)
const stageOrder = computed(() => {
  const all = ['research', 'style', 'outline', 'script', 'content']
  return all.filter(s => (s === 'research' ? researchEnabled.value : s === 'content' ? contentEnabled.value : true))
})

const researchResults = ref([])
const selectedResearch = ref(new Set())
const researchConfirmed = ref(false)
const activeResearchIndex = ref(null)

const stages = reactive({
  research:  { status: 'waiting', content: '', thinking: '' },
  outline:   { status: 'waiting', content: '', thinking: '' },
  content:   { status: 'waiting', content: '', thinking: '' },
  script:    { status: 'waiting', content: '', thinking: '' },
  style:     { status: 'waiting', content: '', thinking: '' },
})

const editedContent = reactive({
  outline: '',
  content: '',
  script: '',
})

function getStageContent(key) {
  return editedContent[key] || stages[key]?.content || ''
}

function renderMarkdown(text) {
  if (!text) return ''
  const cleaned = text
    .replace(/```json[\s\S]*?```/g, '')
    .replace(/```[\s\S]*$/g, '')
    .trim()
  const html = marked.parse(cleaned, { breaks: true })
  return DOMPurify.sanitize(html.replace(/<p>\s*<\/p>/g, '').replace(/<pre><code>\s*<\/code><\/pre>/g, ''))
}

const directionText = computed(() =>
  selectedDirection.value ? `${topic.value} — ${selectedDirection.value.title}` : topic.value
)

const renderedClarifyHtml = computed(() => renderMarkdown(clarifyContent.value))
const renderedAnalysisHtml = computed(() => renderMarkdown(analysis.value))
const renderedStyleHtml = computed(() => renderMarkdown(styleContent.value))

const editableStages = computed(() => stageOrder.value.filter(s => s !== 'research' && s !== 'style'))
const stageMeta = {
  research:  { label: '资料收集',   icon: 'search' },
  outline:   { label: '讲解思路',   icon: 'list' },
  content:   { label: '自媒体文章',   icon: 'edit' },
  style:     { label: '口播风格',   icon: 'palette' },
  script:    { label: '口播稿', icon: 'mic' },
}

const navItems = computed(() => {
  const items = [
    { key: 'direction', label: '创作方向', icon: 'compass', status: getDirectionStatus() },
  ]
  stageOrder.value.forEach(key => {
    items.push({ key, label: stageMeta[key].label, icon: stageMeta[key].icon, status: stages[key].status })
  })
  return items
})

function getDirectionStatus() {
  if (phase.value === 'error') return 'error'
  if (selectedDirection.value) return 'completed'
  if (phase.value === 'analyzing') return 'running'
  return 'waiting'
}

function isItemViewable(key) {
  if (key === 'direction') return options.value.length > 0
  if (key === 'style') return styleOptions.value.length > 0 || stages.style.status === 'running'
  if (key === 'research') return researchResults.value.length > 0 || stages.research.status === 'running' || researchConfirmed.value
  return stages[key].content !== '' || stages[key].thinking !== '' || stages[key].status === 'running'
}

function handleNavClick(key) {
  if (!isItemViewable(key)) return
  userNavigated.value = true
  activeView.value = key
  if (key === 'research') researchConfirmed.value = false
}

watch(currentStage, (stage) => {
  if (stage && !userNavigated.value) {
    activeView.value = stage
  }
})

let navTimeout = null
watch(activeView, () => {
  if (userNavigated.value) {
    clearTimeout(navTimeout)
    navTimeout = setTimeout(() => { userNavigated.value = false }, 8000)
  }
})

const scrollContainer = ref(null)
const scrollToBottom = async () => {
  await nextTick()
  const el = scrollContainer.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
}

watch(() => {
  if (!currentStage.value) return ''
  return stages[currentStage.value]?.content?.length ?? 0
}, () => {
  if (activeView.value === currentStage.value) scrollToBottom()
})

// ── Handlers ───────────────────────────────────────────
function fetchStyleOptions() {
  styleThinking.value = ''
  styleContent.value = ''
  styleOptions.value = []
  selectedStyle.value = null
  pendingStyle.value = null
  currentStage.value = 'style'
  stages.style.status = 'running'
  activeView.value = 'style'
  userNavigated.value = false

  return fetchSSE('/api/style', {
    topic: topic.value,
    direction: directionText.value,
  }, {
    onThinking(data) {
      styleThinking.value += data.thinking || data.token || ''
    },
    onToken(data) {
      styleContent.value += data.token || ''
      stages.style.content = styleContent.value
    },
    onOptions(data) {
      styleOptions.value = data.options || []
      stages.style.status = 'waiting'
      currentStage.value = null
    },
    onStage(data) {
      if (data.stage === 'style') {
        stages.style.status = data.status === 'completed' ? 'completed' : data.status
      }
    },
    onError(err) { handleGenerateError(err) },
  })
}

async function handleTopicSubmit(text) {
  topic.value = text
  phase.value = 'analyzing'
  activeView.value = 'direction'
  userNavigated.value = false
  analyzeThinking.value = ''
  clarifyContent.value = ''
  errorMessage.value = ''

  await fetchSSE('/api/clarify', { topic: text }, {
    onThinking(data) {
      analyzeThinking.value += data.thinking || data.token || ''
    },
    onToken(data) {
      clarifyContent.value += data.token || ''
    },
    onOptions(data) {
      analysis.value = clarifyContent.value || ''
      options.value = data.options || []
    },
    onDone() {
      phase.value = 'select-direction'
    },
    onError(err) {
      console.error('Clarify error:', err)
      const msg = typeof err === 'string' ? err : err?.message || String(err)
      if (msg.includes('503') || msg.includes('busy')) {
        errorMessage.value = 'AI 服务当前繁忙，请稍后再试。'
      } else if (msg.includes('502') || msg.includes('network')) {
        errorMessage.value = '网络连接失败，请检查后端服务是否启动。'
      } else {
        errorMessage.value = '分析失败，请重试或换个主题。'
      }
      phase.value = 'error'
    },
  })
}

async function handleDirectionSelect(opt) {
  selectedDirection.value = opt
  pendingDirection.value = null
  userNavigated.value = false

  stages.outline = { status: 'waiting', content: '', thinking: '' }
  stages.content = { status: 'waiting', content: '', thinking: '' }
  stages.style = { status: 'waiting', content: '', thinking: '' }
  stages.script = { status: 'waiting', content: '', thinking: '' }

  if (!researchEnabled.value) {
    phase.value = 'researching'
    await fetchStyleOptions()
    return
  }

  phase.value = 'researching'
  currentStage.value = 'research'
  activeView.value = 'research'
  researchConfirmed.value = false
  researchResults.value = []
  selectedResearch.value = new Set()
  activeResearchIndex.value = null
  stages.research = { status: 'running', content: '', thinking: '' }

  await fetchSSE('/api/research', { topic: topic.value, direction: directionText.value }, {
    onStage(data) {
      if (data.stage === 'research') {
        stages.research.status = data.status === 'completed' ? 'completed' : 'running'
      }
    },
    onResults(data) {
      researchResults.value = data.results || []
      selectedResearch.value = new Set(data.results.map((_, i) => i))
    },
    onError(err) {
      console.error('Research error:', err)
      errorMessage.value = '资料收集失败，请重试。'
      phase.value = 'error'
    },
  })
}

const researchHtml = ref('')

async function confirmResearch() {
  if (selectedResearch.value.size === 0) return

  const htmlParts = ['<h2>搜索结果</h2>']
  researchResults.value.forEach((r, i) => {
    if (selectedResearch.value.has(i)) htmlParts.push(r.html)
  })
  researchHtml.value = htmlParts.join('')
  researchConfirmed.value = true

  await fetchStyleOptions()
}

function continueToContent() {
  editedContent.script = editedContent.script || stages.script.content
  currentStage.value = 'content'
  stages.content = { status: 'running', content: '', thinking: '' }
  userNavigated.value = false

  fetchSSE('/api/content', {
    topic: topic.value,
    direction: directionText.value,
    research: researchHtml.value,
    outline: editedContent.outline,
    script: editedContent.script,
    style: selectedStyle.value?.title || '',
  }, {
    onStage(data) { if (data.status === 'completed') { stages[data.stage].status = 'completed'; currentStage.value = null; phase.value = 'done' } },
    onToken(data) { stages[data.stage].content += data.token },
    onThinking(data) { stages[data.stage].thinking += data.thinking || data.token || '' },
    onError(err) { handleGenerateError(err) },
  })
}

function resetDownstream(stageKey) {
  const idx = stageOrder.value.indexOf(stageKey)
  if (idx === -1) return
  for (let i = idx + 1; i < stageOrder.value.length; i++) {
    const key = stageOrder.value[i]
    stages[key] = { status: 'waiting', content: '', thinking: '' }
    if (editedContent[key] !== undefined) editedContent[key] = ''
  }
  if (phase.value === 'done') phase.value = 'researching'
}

function continueToScript() {
  editedContent.outline = editedContent.outline || stages.outline.content
  currentStage.value = 'script'
  stages.script = { status: 'running', content: '', thinking: '' }
  resetDownstream('script')
  userNavigated.value = false

  fetchSSE('/api/script', {
    topic: topic.value,
    direction: directionText.value,
    outline: editedContent.outline,
    style: selectedStyle.value?.title || '',
  }, {
    onStage(data) { if (data.status === 'completed') { stages[data.stage].status = 'completed'; currentStage.value = null; if (!contentEnabled.value) phase.value = 'done' } },
    onToken(data) { stages[data.stage].content += data.token },
    onThinking(data) { stages[data.stage].thinking += data.thinking || data.token || '' },
    onError(err) { handleGenerateError(err) },
  })
}

async function handleStyleSelect(opt) {
  selectedStyle.value = opt
  pendingStyle.value = null
  stages.style.status = 'completed'
  currentStage.value = 'outline'
  stages.outline.status = 'running'
  activeView.value = 'outline'
  userNavigated.value = false

  fetchSSE('/api/outline', {
    topic: topic.value,
    direction: directionText.value,
    research: researchHtml.value,
    style: opt.title,
  }, {
    onStage(data) { if (data.status === 'completed') { stages[data.stage].status = 'completed'; currentStage.value = null } },
    onToken(data) { stages[data.stage].content += data.token },
    onThinking(data) { stages[data.stage].thinking += data.thinking || data.token || '' },
    onError(err) { handleGenerateError(err) },
  })
}

function handleGenerateError(err) {
  console.error('Generate error:', err)
  const msg = typeof err === 'string' ? err : err?.message || String(err)
  errorMessage.value = msg.includes('503') || msg.includes('busy')
    ? 'AI 服务当前繁忙，生成中断。'
    : '生成过程中出错，请重试。'
  phase.value = 'error'
}

function toggleResearchItem(index) {
  const newSet = new Set(selectedResearch.value)
  if (newSet.has(index)) newSet.delete(index)
  else newSet.add(index)
  selectedResearch.value = newSet
}

function toggleAllResearch() {
  if (selectedResearch.value.size === researchResults.value.length) {
    selectedResearch.value = new Set()
  } else {
    selectedResearch.value = new Set(researchResults.value.map((_, i) => i))
  }
}

function reset() {
  topic.value = ''
  phase.value = 'input'
  analysis.value = ''
  options.value = []
  selectedDirection.value = null
  currentStage.value = null
  activeView.value = 'direction'
  userNavigated.value = false
  analyzeThinking.value = ''
  clarifyContent.value = ''
  errorMessage.value = ''
  pendingDirection.value = null
  customDirection.value = ''
  isCustomDirection.value = false
  styleOptions.value = []
  selectedStyle.value = null
  pendingStyle.value = null
  customStyle.value = ''
  isCustomStyle.value = false
  styleThinking.value = ''
  styleContent.value = ''
  researchResults.value = []
  selectedResearch.value = new Set()
  researchConfirmed.value = false
  activeResearchIndex.value = null
  Object.keys(stages).forEach(k => {
    stages[k] = { status: 'waiting', content: '', thinking: '' }
  })
  editedContent.outline = ''
  editedContent.content = ''
  editedContent.script = ''
  researchHtml.value = ''
}

const confirmBtnRef = ref(null)

function selectDirection(opt) {
  isCustomDirection.value = false
  customDirection.value = ''
  pendingDirection.value = opt
  nextTick(() => {
    confirmBtnRef.value?.focus()
  })
}

function useCustomDirection() {
  pendingDirection.value = null
  isCustomDirection.value = true
  nextTick(() => {
    confirmBtnRef.value?.focus()
  })
}

function confirmDirection() {
  if (isCustomDirection.value && customDirection.value.trim()) {
    handleDirectionSelect({ id: '★', title: customDirection.value.trim() })
  } else if (pendingDirection.value) {
    handleDirectionSelect(pendingDirection.value)
  }
}

function changeDirection() {
  pendingDirection.value = null
  isCustomDirection.value = false
  customDirection.value = ''
}

const confirmStyleBtnRef = ref(null)

function selectStyle(opt) {
  isCustomStyle.value = false
  customStyle.value = ''
  pendingStyle.value = opt
  nextTick(() => {
    confirmStyleBtnRef.value?.focus()
  })
}

function useCustomStyle() {
  pendingStyle.value = null
  isCustomStyle.value = true
  nextTick(() => {
    confirmStyleBtnRef.value?.focus()
  })
}

function confirmStyle() {
  if (isCustomStyle.value && customStyle.value.trim()) {
    handleStyleSelect({ id: '★', title: customStyle.value.trim() })
  } else if (pendingStyle.value) {
    handleStyleSelect(pendingStyle.value)
  }
}

function changeStyle() {
  pendingStyle.value = null
  isCustomStyle.value = false
  customStyle.value = ''
}

function retry() {
  if (selectedDirection.value) {
    handleDirectionSelect(selectedDirection.value)
  } else {
    handleTopicSubmit(topic.value)
  }
}

const toast = ref('')

let toastTimer = null
function showToast(msg) {
  toast.value = msg
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => { toast.value = '' }, 1500)
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {
    const ta = document.createElement('textarea')
    ta.value = text
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
  }
  showToast('已复制到剪贴板')
}

function stripSubtitle(text) {
  return text
    .replace(/^（[^）]*）$\n?/gm, '')
    .replace(/\*\*([^*]*)\*\*/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

async function copyScript() {
  const text = contentEnabled.value
    ? (editedContent.content || stages.content.content)
    : (editedContent.script || stages.script.content)
  await copyToClipboard(text)
}

async function copyAsSubtitle() {
  const text = editedContent.script || stages.script.content
  await copyToClipboard(stripSubtitle(text))
}

;(async () => {
  try {
    const res = await fetch('/api/config')
    if (res.ok) {
      const cfg = await res.json()
      researchEnabled.value = cfg.researchEnabled ?? true
      contentEnabled.value = cfg.contentEnabled ?? true
    }
  } catch { /* use defaults */ }
})()
</script>

<template>
  <div class="min-h-screen bg-bg-base flex">
    <!-- ═══ Sidebar ═══ -->
    <aside
      v-if="phase !== 'input'"
      class="w-60 flex-shrink-0 bg-white border-r border-border-subtle flex flex-col h-screen sticky top-0"
    >
      <!-- Brand -->
      <div class="px-5 pt-5 pb-4 border-b border-border-subtle">
        <div class="flex items-center justify-between">
          <h1 class="text-base font-bold text-fg tracking-tight font-display">ScriptPilot</h1>
          <button
            @click="reset"
            class="p-1.5 rounded-lg text-fg-dim hover:text-fg-secondary hover:bg-surface-hover transition-all duration-200"
            title="新主题"
          >
            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
            </svg>
          </button>
        </div>
        <p class="mt-2 text-xs text-fg-secondary leading-relaxed line-clamp-2">{{ topic }}</p>
      </div>

      <!-- Nav items -->
      <nav class="flex-1 py-3 px-3 space-y-1 overflow-y-auto">
        <button
          v-for="item in navItems"
          :key="item.key"
          @click="handleNavClick(item.key)"
          :disabled="!isItemViewable(item.key)"
          class="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-150 group"
          :class="[
            activeView === item.key
              ? 'bg-accent/8 text-accent border border-accent/15'
              : isItemViewable(item.key)
                ? 'text-fg-secondary hover:bg-surface-hover hover:text-fg border border-transparent'
                : 'text-fg-dim cursor-not-allowed border border-transparent',
          ]"
        >
          <!-- Status indicator -->
          <span
            class="flex-shrink-0 w-5 h-5 rounded-md flex items-center justify-center"
            :class="{
              'bg-green-500/10 text-green-600': item.status === 'completed',
              'bg-accent/10 text-accent': item.status === 'running',
              'bg-red-100 text-red-500': item.status === 'error',
              'bg-surface text-fg-dim': item.status === 'waiting',
            }"
          >
            <svg v-if="item.status === 'completed'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
            <svg v-else-if="item.status === 'error'" class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <svg v-else-if="item.status === 'running'" class="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span v-else class="w-1.5 h-1.5 rounded-full bg-fg-dim/50"></span>
          </span>

          <div class="min-w-0">
            <span class="text-sm font-medium truncate block">{{ item.label }}</span>
            <span v-if="item.status === 'running'" class="text-[11px] text-accent/70 block mt-0.5">
              {{ item.key === 'research' ? '收集中...' : (stages[item.key]?.thinking && !stages[item.key]?.content ? '正在思考...' : '正在生成...') }}
            </span>
          </div>
        </button>
      </nav>

      <!-- Bottom: copy / retry -->
      <div v-if="phase === 'error'" class="px-4 pb-4 pt-2 border-t border-red-100">
        <button
          @click="retry"
          class="w-full flex items-center justify-center gap-2 px-3 py-2.5 bg-red-600 text-white text-sm font-medium rounded-xl hover:bg-red-700 transition-colors active:scale-[0.98]"
        >
          重试
        </button>
      </div>
    </aside>

    <!-- ═══ Main Content ═══ -->
    <!-- Phase: Initial Input -->
    <main v-if="phase === 'input'" class="flex-1">
      <TopicInput @submit="handleTopicSubmit" />
    </main>

    <!-- Phase: Sidebar + Content -->
    <main v-else class="flex-1 h-screen overflow-y-auto" ref="scrollContainer">
      <div :class="activeView === 'research' && !researchConfirmed
        ? 'px-8 py-6 h-full flex flex-col'
        : editableStages.includes(activeView) && stages[activeView]?.content
          ? 'px-6 py-6 h-full'
          : 'max-w-3xl mx-auto px-6 py-6'">

        <!-- ── View: Direction ── -->
        <template v-if="activeView === 'direction'">
          <!-- Error state -->
          <div v-if="phase === 'error'" class="animate-fade-in">
            <div class="flex items-start gap-4 p-6 bg-red-50 border border-red-200 rounded-2xl">
              <div class="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 flex items-center justify-center">
                <svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div class="flex-1">
                <h3 class="text-sm font-semibold text-red-800 mb-1">生成失败</h3>
                <p class="text-sm text-red-600 leading-relaxed">{{ errorMessage }}</p>
                <div class="flex gap-3 mt-4">
                  <button
                    @click="retry"
                    class="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors active:scale-95"
                  >
                    重试
                  </button>
                  <button
                    @click="reset"
                    class="px-4 py-2 bg-white text-red-600 text-sm font-medium rounded-lg border border-red-200 hover:bg-red-50 transition-colors"
                  >
                    换个主题
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Analyzing state: thinking phase -->
          <ThinkingIndicator v-if="phase === 'analyzing' && !clarifyContent" :thinking="analyzeThinking" class="animate-fade-in" />

          <!-- Analyzing state: streaming LLM output -->
          <div v-if="phase === 'analyzing' && clarifyContent" class="animate-fade-in">
            <div class="prose-content text-sm text-fg-secondary" v-html="renderedClarifyHtml"></div>
          </div>

          <!-- Direction selection -->
          <div v-if="options.length > 0" class="animate-fade-in">
            <div class="prose-content text-sm text-fg-secondary" v-html="renderedAnalysisHtml"></div>

            <!-- Already confirmed & generating -->
            <div v-if="selectedDirection" class="mb-6">
              <p class="text-xs text-fg-dim mb-3">已选择方向</p>
              <div class="p-4 rounded-xl bg-accent/5 border border-accent/20">
                <div class="flex items-center gap-3">
                  <span class="flex-shrink-0 w-7 h-7 rounded-lg bg-accent text-white flex items-center justify-center text-xs font-bold">
                    {{ selectedDirection.id }}
                  </span>
                  <h4 class="text-sm font-medium text-fg">{{ selectedDirection.title }}</h4>
                </div>
              </div>
            </div>

            <!-- Confirm pending selection -->
            <div v-else-if="pendingDirection" class="animate-fade-in">
              <p class="text-xs text-fg-dim mb-3">确认创作方向</p>
              <div class="p-4 rounded-xl bg-accent/5 border-2 border-accent/20">
                <div class="flex items-center gap-3">
                  <span class="flex-shrink-0 w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center text-sm font-bold">
                    {{ pendingDirection.id }}
                  </span>
                  <h4 class="text-base font-semibold text-fg">{{ pendingDirection.title }}</h4>
                </div>
              </div>
              <div class="flex gap-3 mt-5">
                <button
                  ref="confirmBtnRef"
                  @click="confirmDirection"
                  class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all duration-200 active:scale-95"
                >
                  确认
                </button>
                <button
                  @click="changeDirection"
                  class="px-6 py-2.5 bg-white text-fg-secondary text-sm font-medium rounded-xl border border-border-subtle hover:border-border hover:text-fg transition-all duration-200"
                >
                  修改
                </button>
              </div>
            </div>

            <!-- Direction cards (selectable) -->
            <template v-if="phase === 'select-direction' && !pendingDirection && !selectedDirection && !isCustomDirection">
              <p class="text-xs text-fg-dim mb-3">选择一个创作方向：</p>
              <div class="space-y-2">
                <button
                  v-for="opt in options"
                  :key="opt.id"
                  @click="selectDirection(opt)"
                  class="w-full text-left px-4 py-3 rounded-xl border border-border-subtle hover:border-accent/40 hover:bg-surface-hover cursor-pointer transition-all duration-200 group active:scale-[0.98]"
                >
                  <div class="flex items-center gap-3">
                    <span class="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold bg-accent/15 text-accent-light group-hover:bg-accent group-hover:text-white transition-colors">
                      {{ opt.id }}
                    </span>
                    <h4 class="text-sm font-medium text-fg group-hover:text-accent-light transition-colors">{{ opt.title }}</h4>
                  </div>
                </button>
                <button
                  @click="useCustomDirection"
                  class="w-full text-left px-4 py-3 rounded-xl border border-dashed border-border-subtle hover:border-accent/40 hover:bg-surface-hover cursor-pointer transition-all duration-200 group"
                >
                  <div class="flex items-center gap-3">
                    <span class="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-fg-dim group-hover:text-accent transition-colors">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </span>
                    <h4 class="text-sm text-fg-dim group-hover:text-accent transition-colors">自己写一个方向</h4>
                  </div>
                </button>
              </div>
            </template>

            <!-- Custom direction input -->
            <template v-if="phase === 'select-direction' && isCustomDirection && !selectedDirection">
              <p class="text-xs text-fg-dim mb-3">输入你的创作方向：</p>
              <div class="p-4 rounded-xl bg-accent/5 border-2 border-accent/20">
                <input
                  ref="confirmBtnRef"
                  v-model="customDirection"
                  @keydown.enter="confirmDirection"
                  placeholder="例如：从产品经理视角拆解 AI 工具的实际价值"
                  class="w-full bg-transparent text-fg text-sm placeholder-fg-dim focus:outline-none"
                />
              </div>
              <div class="flex gap-3 mt-5">
                <button
                  @click="confirmDirection"
                  :disabled="!customDirection.trim()"
                  class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all duration-200 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  确认
                </button>
                <button
                  @click="changeDirection"
                  class="px-6 py-2.5 bg-white text-fg-secondary text-sm font-medium rounded-xl border border-border-subtle hover:border-border hover:text-fg transition-all duration-200"
                >
                  返回选择
                </button>
              </div>
            </template>
          </div>
        </template>

        <!-- ── View: Style Selection ── -->
        <template v-else-if="activeView === 'style'">
          <!-- Thinking phase -->
          <ThinkingIndicator v-if="stages.style.status === 'running' && !styleContent" :thinking="styleThinking" class="animate-fade-in" />

          <!-- Streaming LLM output -->
          <div v-if="styleContent && !styleOptions.length" class="animate-fade-in">
            <div class="prose-content text-sm text-fg-secondary" v-html="renderedStyleHtml"></div>
          </div>

          <!-- Style selection -->
          <div v-if="styleOptions.length > 0" class="animate-fade-in">
            <div v-if="styleContent" class="prose-content text-sm text-fg-secondary mb-4" v-html="renderedStyleHtml"></div>

            <!-- Already confirmed & generating script -->
            <div v-if="selectedStyle" class="mb-6">
              <p class="text-xs text-fg-dim mb-3">已选择风格</p>
              <div class="p-4 rounded-xl bg-accent/5 border border-accent/20">
                <div class="flex items-center gap-3">
                  <span class="flex-shrink-0 w-7 h-7 rounded-lg bg-accent text-white flex items-center justify-center text-xs font-bold">
                    {{ selectedStyle.id }}
                  </span>
                  <h4 class="text-sm font-medium text-fg">{{ selectedStyle.title }}</h4>
                </div>
              </div>
            </div>

            <!-- Confirm pending selection -->
            <div v-else-if="pendingStyle" class="animate-fade-in">
              <p class="text-xs text-fg-dim mb-3">确认口播风格</p>
              <div class="p-4 rounded-xl bg-accent/5 border-2 border-accent/20">
                <div class="flex items-center gap-3">
                  <span class="flex-shrink-0 w-8 h-8 rounded-lg bg-accent text-white flex items-center justify-center text-sm font-bold">
                    {{ pendingStyle.id }}
                  </span>
                  <h4 class="text-base font-semibold text-fg">{{ pendingStyle.title }}</h4>
                </div>
              </div>
              <div class="flex gap-3 mt-5">
                <button
                  ref="confirmStyleBtnRef"
                  @click="confirmStyle"
                  class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all duration-200 active:scale-95"
                >
                  确认
                </button>
                <button
                  @click="changeStyle"
                  class="px-6 py-2.5 bg-white text-fg-secondary text-sm font-medium rounded-xl border border-border-subtle hover:border-border hover:text-fg transition-all duration-200"
                >
                  修改
                </button>
              </div>
            </div>

            <!-- Style cards (selectable) -->
            <template v-if="!pendingStyle && !selectedStyle && !isCustomStyle">
              <p class="text-xs text-fg-dim mb-3">选择一个口播风格：</p>
              <div class="space-y-2">
                <button
                  v-for="opt in styleOptions"
                  :key="opt.id"
                  @click="selectStyle(opt)"
                  class="w-full text-left px-4 py-3 rounded-xl border border-border-subtle hover:border-accent/40 hover:bg-surface-hover cursor-pointer transition-all duration-200 group active:scale-[0.98]"
                >
                  <div class="flex items-center gap-3">
                    <span class="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold bg-accent/15 text-accent-light group-hover:bg-accent group-hover:text-white transition-colors">
                      {{ opt.id }}
                    </span>
                    <h4 class="text-sm font-medium text-fg group-hover:text-accent-light transition-colors">{{ opt.title }}</h4>
                  </div>
                </button>
                <button
                  @click="useCustomStyle"
                  class="w-full text-left px-4 py-3 rounded-xl border border-dashed border-border-subtle hover:border-accent/40 hover:bg-surface-hover cursor-pointer transition-all duration-200 group"
                >
                  <div class="flex items-center gap-3">
                    <span class="flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center text-fg-dim group-hover:text-accent transition-colors">
                      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </span>
                    <h4 class="text-sm text-fg-dim group-hover:text-accent transition-colors">自己写一个风格</h4>
                  </div>
                </button>
              </div>
            </template>

            <!-- Custom style input -->
            <template v-if="isCustomStyle && !selectedStyle">
              <p class="text-xs text-fg-dim mb-3">输入你想要的口播风格：</p>
              <div class="p-4 rounded-xl bg-accent/5 border-2 border-accent/20">
                <input
                  ref="confirmStyleBtnRef"
                  v-model="customStyle"
                  @keydown.enter="confirmStyle"
                  placeholder="例如：像和老朋友聊天一样轻松自然"
                  class="w-full bg-transparent text-fg text-sm placeholder-fg-dim focus:outline-none"
                />
              </div>
              <div class="flex gap-3 mt-5">
                <button
                  @click="confirmStyle"
                  :disabled="!customStyle.trim()"
                  class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all duration-200 active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  确认
                </button>
                <button
                  @click="changeStyle"
                  class="px-6 py-2.5 bg-white text-fg-secondary text-sm font-medium rounded-xl border border-border-subtle hover:border-border hover:text-fg transition-all duration-200"
                >
                  返回选择
                </button>
              </div>
            </template>
          </div>
        </template>

        <!-- ── View: Pipeline Stage ── -->
        <template v-else>
          <!-- Error banner during pipeline -->
          <div v-if="phase === 'error'" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 animate-fade-in">
            <svg class="w-5 h-5 text-red-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <p class="text-sm text-red-600 flex-1">{{ errorMessage }}</p>
            <button @click="retry" class="px-3 py-1.5 bg-red-600 text-white text-xs font-medium rounded-lg hover:bg-red-700 transition-colors">重试</button>
          </div>

          <!-- Research selection view -->
          <div v-if="activeView === 'research' && !researchConfirmed" class="animate-fade-in flex flex-col flex-1 min-h-0">
            <ThinkingIndicator v-if="stages.research.status === 'running' && researchResults.length === 0" label="收集中..." :thinking="stages.research.thinking" />

            <!-- Results header + split panel -->
            <template v-if="researchResults.length > 0">
              <div class="flex items-center justify-between flex-shrink-0 mb-4">
                <p class="text-sm text-fg-secondary">
                  已选 {{ selectedResearch.size }} / {{ researchResults.length }} 条
                </p>
                <button @click="toggleAllResearch" class="text-xs text-accent hover:underline">
                  {{ selectedResearch.size === researchResults.length ? '取消全选' : '全选' }}
                </button>
              </div>

              <!-- Split panel fills remaining space -->
              <div class="flex gap-6 flex-1 min-h-0">
                <!-- Left: title list -->
                <div class="w-[380px] flex-shrink-0 flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white">
                  <div class="flex-1 overflow-y-auto px-2 py-1">
                    <div
                      v-for="(result, i) in researchResults"
                      :key="i"
                      @click="activeResearchIndex = i"
                      class="flex items-start gap-3 px-4 py-3 cursor-pointer transition-all duration-150 rounded-xl my-0.5"
                      :class="activeResearchIndex === i
                        ? 'bg-accent/8'
                        : 'hover:bg-surface-hover'"
                    >
                      <input
                        type="checkbox"
                        :checked="selectedResearch.has(i)"
                        @click.stop="toggleResearchItem(i)"
                        class="mt-1 w-4 h-4 rounded accent-accent cursor-pointer flex-shrink-0"
                      />
                      <div class="min-w-0 flex-1">
                        <span class="text-[13px] text-fg leading-relaxed line-clamp-2">{{ result.title }}</span>
                      </div>
                    </div>
                  </div>

                  <!-- Confirm bar -->
                  <div class="px-5 py-4 border-t border-border-subtle bg-white">
                    <button
                      @click="confirmResearch"
                      :disabled="selectedResearch.size === 0"
                      class="w-full px-4 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
                    >
                      确认（{{ selectedResearch.size }} 条）
                    </button>
                    <p class="text-xs text-fg-dim text-center mt-2">仅使用选中资料继续生成</p>
                  </div>
                </div>

                <!-- Right: detail panel -->
                <div class="flex-1 min-w-0 border border-border-subtle rounded-2xl overflow-y-auto bg-white">
                  <template v-if="activeResearchIndex !== null && researchResults[activeResearchIndex]">
                    <div class="p-6">
                      <div class="flex items-start justify-between gap-3 mb-5">
                        <h3 class="text-base font-semibold text-fg leading-snug">{{ researchResults[activeResearchIndex].title }}</h3>
                        <span class="text-xs font-bold text-accent bg-accent/10 px-2.5 py-1 rounded-full flex-shrink-0">#{{ researchResults[activeResearchIndex].index }}</span>
                      </div>
                      <div class="text-sm text-fg-secondary leading-relaxed whitespace-pre-wrap mb-6">{{ researchResults[activeResearchIndex].content }}</div>
                      <div class="pt-4 border-t border-border-subtle">
                        <a
                          :href="researchResults[activeResearchIndex].url"
                          target="_blank"
                          class="inline-flex items-center gap-2 text-sm text-accent hover:text-accent-light transition-colors"
                        >
                          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                          </svg>
                          查看原始网页
                        </a>
                      </div>
                    </div>
                  </template>
                  <template v-else>
                    <div class="flex flex-col items-center justify-center h-full text-fg-dim">
                      <svg class="w-12 h-12 mb-3 opacity-20" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                      <p class="text-sm">点击左侧条目查看详情</p>
                    </div>
                  </template>
                </div>
              </div>
            </template>

            <!-- Empty results -->
            <div v-if="stages.research.status === 'completed' && researchResults.length === 0" class="text-center py-8">
              <p class="text-sm text-fg-secondary mb-4">未找到相关资料</p>
              <button @click="confirmResearch" class="px-4 py-2 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-colors">
                直接继续
              </button>
            </div>
          </div>

          <!-- Regular pipeline stage view -->
          <div v-else :key="activeView" class="animate-fade-in">
            <!-- Outline/Content/Script: split panel editor -->
            <MarkdownSplitPanel
              :model-value="getStageContent(activeView)"
              @update:model-value="(val) => { editedContent[activeView] = val }"
              :status="stages[activeView]?.status"
              :thinking="stages[activeView]?.thinking"
            >
              <template v-if="activeView === 'outline' && stages.outline.status === 'completed'" #action>
                <button @click="continueToScript" class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98]">
                  确认思路，继续生成口播稿
                </button>
              </template>
              <template v-if="activeView === 'script' && stages.script.status === 'completed'" #action>
                <div class="flex items-center gap-3">
                  <button v-if="contentEnabled" @click="continueToContent" class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98]">
                    确认口播稿，继续生成文章
                  </button>
                  <button @click="copyScript" class="flex items-center justify-center gap-2 px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98]">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    复制口播稿
                  </button>
                  <button @click="copyAsSubtitle" class="flex items-center justify-center gap-2 px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98]">
                    复制为字幕
                  </button>
                </div>
              </template>
              <template v-if="activeView === 'content' && stages.content.status === 'completed'" #action>
                <div class="flex items-center gap-3">
                  <button @click="continueToContent" class="px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98]">
                    重新生成文章
                  </button>
                  <button @click="copyScript" class="flex items-center justify-center gap-2 px-6 py-2.5 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98]">
                    <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    复制文章
                  </button>
                </div>
              </template>
            </MarkdownSplitPanel>
          </div>
        </template>

      </div>
    </main>

    <Transition name="toast">
      <div v-if="toast" class="fixed bottom-8 left-1/2 -translate-x-1/2 px-5 py-2.5 bg-fg/85 text-white text-sm font-medium rounded-xl shadow-lg shadow-fg/10 pointer-events-none backdrop-blur-sm">
        {{ toast }}
      </div>
    </Transition>
  </div>
</template>

<style>
/* Fade in animation */
.animate-fade-in {
  animation: fadeIn 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* Floating background orbs */
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -25px) scale(1.05); }
  66% { transform: translate(-15px, 15px) scale(0.97); }
}
.animate-float {
  animation: float 12s ease-in-out infinite;
}
.animate-float-delayed {
  animation: float 15s ease-in-out 3s infinite;
}
.animate-float-slow {
  animation: float 18s ease-in-out 6s infinite;
}

/* Toast */
.toast-enter-active { transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
.toast-leave-active { transition: all 0.2s ease-in; }
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translate(-50%, 12px);
}

/* Hide scrollbar for thinking content */
.scrollbar-hidden {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hidden::-webkit-scrollbar {
  display: none;
}

/* Custom scrollbar */
.overflow-y-auto::-webkit-scrollbar {
  width: 5px;
}
.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}
.overflow-y-auto::-webkit-scrollbar-thumb {
  background: rgba(44, 32, 20, 0.08);
  border-radius: 10px;
}
.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: rgba(44, 32, 20, 0.15);
}
</style>
