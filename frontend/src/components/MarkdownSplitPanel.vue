<script setup>
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import ThinkingIndicator from './ThinkingIndicator.vue'
import '../assets/prose.css'

const props = defineProps({
  modelValue: { type: String, default: '' },
  status: { type: String, default: 'waiting' },
  thinking: { type: String, default: '' },
  simple: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)
const previewRef = ref(null)
const renderedHtml = ref('')
const isEditing = ref(false)
let rafPending = false

function updateHtml() {
  renderedHtml.value = props.modelValue
    ? DOMPurify.sanitize(marked.parse(props.modelValue, { breaks: true }))
    : ''
}

function scheduleScroll(el) {
  if (!el || rafPending) return
  rafPending = true
  requestAnimationFrame(() => {
    el.scrollTop = el.scrollHeight
    rafPending = false
  })
}

watch(() => props.modelValue, () => {
  updateHtml()
  if (props.status === 'running') {
    scheduleScroll(previewRef.value)
    scheduleScroll(textareaRef.value)
  }
}, { immediate: true })

watch(() => props.status, (s) => {
  if (s === 'running') isEditing.value = false
  if (s === 'completed') updateHtml()
})

function onInput(e) {
  emit('update:modelValue', e.target.value)
}

function toggleEdit() {
  isEditing.value = !isEditing.value
  if (isEditing.value) {
    nextTick(() => {
      if (textareaRef.value) textareaRef.value.focus()
    })
  }
}
</script>

<template>
  <ThinkingIndicator v-if="status === 'running' && !modelValue" :thinking="thinking" />

  <!-- Simple mode: preview only with edit toggle -->
  <div v-else-if="simple && modelValue" class="max-w-5xl mx-auto" style="height: calc(100vh - 140px)">
    <!-- Edit mode -->
    <div v-if="isEditing" class="h-full flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white shadow-sm">
      <div class="px-4 py-2.5 border-b border-border-subtle bg-bg-base/40">
        <span class="text-[11px] text-accent font-medium">可编辑</span>
      </div>
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="onInput"
        class="flex-1 w-full p-4 text-sm leading-relaxed resize-none focus:outline-none text-fg"
        spellcheck="false"
      />
    </div>

    <!-- Preview mode -->
    <div v-else class="h-full flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white shadow-sm">
      <div class="px-4 py-2.5 border-b border-border-subtle bg-bg-base/40">
        <span v-if="status === 'completed'" class="text-[11px] text-accent font-medium">可编辑</span>
        <span v-else class="text-xs font-semibold text-fg-dim tracking-wide uppercase">生成中</span>
      </div>
      <div ref="previewRef" class="flex-1 overflow-y-auto p-6">
        <div class="prose-content" v-html="renderedHtml"></div>
      </div>
    </div>
  </div>

  <!-- Split panel (default mode) -->
  <div v-else-if="modelValue" class="flex gap-4" style="height: calc(100vh - 120px)">
    <div class="w-1/2 flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white shadow-sm">
      <div class="flex items-center justify-between px-4 py-2.5 border-b border-border-subtle bg-bg-base/40">
        <span class="text-xs font-semibold text-fg-dim tracking-wide uppercase">Markdown</span>
        <span v-if="status === 'completed'" class="text-[11px] text-accent font-medium">可编辑</span>
      </div>
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="onInput"
        :readonly="status === 'running'"
        class="flex-1 w-full p-4 text-sm font-mono leading-relaxed resize-none focus:outline-none text-fg"
        :class="{ 'bg-bg-base/30': status === 'running' }"
        spellcheck="false"
      />
    </div>
    <div class="w-1/2 flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white shadow-sm">
      <div class="px-4 py-2.5 border-b border-border-subtle bg-bg-base/40">
        <span class="text-xs font-semibold text-fg-dim tracking-wide uppercase">预览</span>
      </div>
      <div ref="previewRef" class="flex-1 overflow-y-auto p-6">
        <div class="prose-content" v-html="renderedHtml"></div>
      </div>
    </div>
  </div>

  <!-- Action slot below panel, with edit toggle for simple mode -->
  <div v-if="$slots.action || (simple && status === 'completed' && modelValue)" class="mt-4 flex items-center justify-center gap-3">
    <button v-if="simple && status === 'completed' && modelValue" @click="toggleEdit" class="flex items-center gap-1.5 px-5 py-2.5 border border-accent/30 text-accent text-sm font-medium rounded-xl hover:bg-accent/5 transition-all active:scale-[0.98]">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
      </svg>
      {{ isEditing ? '预览' : '编辑' }}
    </button>
    <slot name="action"></slot>
  </div>
</template>
