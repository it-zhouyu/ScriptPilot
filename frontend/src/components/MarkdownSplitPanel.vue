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
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)
const renderedHtml = ref('')
let renderTimeout = null

function updateHtml() {
  renderedHtml.value = props.modelValue
    ? DOMPurify.sanitize(marked.parse(props.modelValue, { breaks: true }))
    : ''
}

watch(() => props.modelValue, () => {
  if (props.status === 'running' && renderedHtml.value) {
    clearTimeout(renderTimeout)
    renderTimeout = setTimeout(updateHtml, 100)
  } else {
    updateHtml()
  }
}, { immediate: true })

function onInput(e) {
  emit('update:modelValue', e.target.value)
}

watch(() => props.modelValue, () => {
  if (props.status === 'running' && textareaRef.value) {
    nextTick(() => {
      textareaRef.value.scrollTop = textareaRef.value.scrollHeight
    })
  }
})
</script>

<template>
  <ThinkingIndicator v-if="status === 'running' && !modelValue" :thinking="thinking" />

  <!-- Split panel -->
  <div v-else-if="modelValue" class="flex gap-4" style="height: calc(100vh - 120px)">
    <!-- Left: markdown source -->
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

    <!-- Right: rendered preview -->
    <div class="w-1/2 flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white shadow-sm">
      <div class="px-4 py-2.5 border-b border-border-subtle bg-bg-base/40">
        <span class="text-xs font-semibold text-fg-dim tracking-wide uppercase">预览</span>
      </div>
      <div class="flex-1 overflow-y-auto p-6">
        <div class="prose-content" v-html="renderedHtml"></div>
      </div>
    </div>
  </div>

  <!-- Action slot below split panel -->
  <div v-if="$slots.action" class="mt-4 flex justify-center">
    <slot name="action"></slot>
  </div>
</template>
