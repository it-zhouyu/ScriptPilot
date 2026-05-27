<script setup>
import { ref, nextTick, watch } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const emit = defineEmits(['back'])

const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const messagesContainer = ref(null)
const expandedReasoning = ref(new Set())

function toggleReasoning(index) {
  const s = new Set(expandedReasoning.value)
  if (s.has(index)) s.delete(index)
  else s.add(index)
  expandedReasoning.value = s
}

function renderMarkdown(text) {
  if (!text) return ''
  const html = marked.parse(text, { breaks: true })
  return DOMPurify.sanitize(html)
}

async function scrollToBottom() {
  await nextTick()
  const el = messagesContainer.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' })
}

watch(() => messages.value.length, scrollToBottom)
watch(() => {
  const last = messages.value[messages.value.length - 1]
  return (last?.content?.length ?? 0) + (last?.reasoning?.length ?? 0)
}, scrollToBottom)

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  isLoading.value = true

  messages.value.push({ role: 'assistant', content: '', reasoning: '' })
  const assistantMsg = messages.value[messages.value.length - 1]

  try {
    const response = await fetch('/api/agent/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: messages.value.slice(0, -1) }),
    })

    if (!response.ok) throw new Error(`HTTP ${response.status}`)

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let currentEvent = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('event: ')) {
          currentEvent = line.slice(7).trim()
        } else if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            if (currentEvent === 'reasoning' && data.token) {
              assistantMsg.reasoning += data.token
            } else if (currentEvent === 'token' && data.token) {
              assistantMsg.content += data.token
            }
          } catch { /* skip malformed */ }
        }
      }
    }
  } catch (err) {
    assistantMsg.content = assistantMsg.content || '抱歉，连接出现问题，请稍后再试。'
  } finally {
    isLoading.value = false
  }
}

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function autoResize(e) {
  const el = e.target
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 120) + 'px'
}
</script>

<template>
  <div class="flex flex-col h-screen bg-bg-base">
    <!-- Header -->
    <header class="flex-shrink-0 px-6 py-4 border-b border-border-subtle bg-white flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button
          @click="emit('back')"
          class="p-2 rounded-lg text-fg-dim hover:text-fg-secondary hover:bg-surface-hover transition-all"
          title="返回"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <div>
          <h1 class="text-base font-bold text-fg font-display">ScriptPilot Agent</h1>
          <p class="text-xs text-fg-dim mt-0.5">与 AI Agent 对话，让 AI 帮你完成创作任务</p>
        </div>
      </div>
      <div class="flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
        <span class="text-xs text-fg-dim">在线</span>
      </div>
    </header>

    <!-- Messages -->
    <div ref="messagesContainer" class="flex-1 overflow-y-auto px-6 py-6 space-y-6">
      <!-- Empty state -->
      <div v-if="messages.length === 0" class="flex flex-col items-center justify-center h-full text-center">
        <div class="w-16 h-16 rounded-2xl bg-accent/10 flex items-center justify-center mb-5">
          <svg class="w-8 h-8 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h2 class="text-lg font-semibold text-fg mb-2">开始对话</h2>
        <p class="text-sm text-fg-secondary max-w-sm">告诉 AI Agent 你的创作需求，它会帮你完成从选题到成稿的全流程。</p>
        <div class="mt-6 flex flex-wrap justify-center gap-2">
          <button
            v-for="hint in ['帮我写一个关于 AI 编程的口播稿', '我想做一个短视频，主题是职场成长', '帮我分析一下最近的科技热点话题']"
            :key="hint"
            @click="inputText = hint"
            class="px-3 py-1.5 text-xs text-fg-secondary border border-border-subtle rounded-lg bg-white/60 hover:bg-white hover:border-accent/30 hover:text-accent transition-colors"
          >
            {{ hint }}
          </button>
        </div>
      </div>

      <!-- Message list -->
      <template v-for="(msg, i) in messages" :key="i">
        <!-- User message -->
        <div v-if="msg.role === 'user'" class="flex justify-end">
          <div class="max-w-[70%] px-4 py-3 bg-accent text-white text-sm rounded-2xl rounded-br-md leading-relaxed whitespace-pre-wrap">
            {{ msg.content }}
          </div>
        </div>

        <!-- Assistant message -->
        <div v-else class="flex items-start gap-3">
          <div class="flex-shrink-0 w-8 h-8 rounded-xl bg-accent/10 flex items-center justify-center">
            <svg class="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
            </svg>
          </div>
          <div class="max-w-[75%] space-y-2">
            <!-- Reasoning block (collapsed by default) -->
            <div v-if="msg.reasoning" class="px-3 py-2 bg-amber-50 border border-amber-200/60 rounded-xl text-xs leading-relaxed">
              <button @click="toggleReasoning(i)" class="flex items-center gap-1.5 text-amber-600 font-medium w-full text-left">
                <svg v-if="!msg.content" class="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                <svg v-else class="w-3 h-3 transition-transform" :class="{ 'rotate-90': expandedReasoning.has(i) }" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                <span>{{ msg.content ? '思考过程' : '思考中...' }}</span>
              </button>
              <p v-if="expandedReasoning.has(i)" class="text-amber-800/70 whitespace-pre-wrap mt-1.5">{{ msg.reasoning }}</p>
            </div>
            <!-- Content block -->
            <div v-if="msg.content || !msg.reasoning" class="px-4 py-3 bg-white text-sm rounded-2xl rounded-bl-md border border-border-subtle leading-relaxed">
              <div v-if="msg.content" class="prose-content" v-html="renderMarkdown(msg.content)"></div>
              <div v-else class="flex items-center gap-1.5 py-1">
                <span class="w-1.5 h-1.5 rounded-full bg-accent/60 animate-bounce" style="animation-delay: 0ms"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-accent/60 animate-bounce" style="animation-delay: 150ms"></span>
                <span class="w-1.5 h-1.5 rounded-full bg-accent/60 animate-bounce" style="animation-delay: 300ms"></span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Input area -->
    <div class="flex-shrink-0 px-6 py-4 border-t border-border-subtle bg-white">
      <div class="flex items-end gap-3 max-w-4xl mx-auto">
        <div class="flex-1 relative">
          <textarea
            v-model="inputText"
            @keydown="handleKeydown"
            placeholder="输入消息，与 AI Agent 对话..."
            rows="1"
            class="w-full bg-bg-base text-fg placeholder-fg-dim px-4 py-3 text-sm rounded-xl border border-border-subtle focus:border-accent/40 focus:ring-2 focus:ring-accent/10 resize-none focus:outline-none transition-all"
            style="max-height: 120px"
            @input="autoResize"
          ></textarea>
        </div>
        <button
          @click="sendMessage"
          :disabled="!inputText.trim() || isLoading"
          class="flex-shrink-0 p-3 bg-accent text-white rounded-xl hover:bg-accent-light disabled:opacity-30 disabled:cursor-not-allowed transition-all active:scale-95"
        >
          <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>
