<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { marked } from 'marked'
import '../assets/prose.css'

const props = defineProps({
  modelValue: { type: String, default: '' },
  status: { type: String, default: 'waiting' },
  thinking: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const textareaRef = ref(null)
const thinkingEl = ref(null)

const renderedHtml = computed(() => {
  if (!props.modelValue) return ''
  return marked.parse(props.modelValue, { breaks: true })
})

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

watch(() => props.thinking, () => {
  if (thinkingEl.value) {
    nextTick(() => {
      thinkingEl.value.scrollTop = thinkingEl.value.scrollHeight
    })
  }
})
</script>

<template>
  <!-- Thinking phase -->
  <div v-if="status === 'running' && !modelValue" class="flex items-center justify-center" style="height: calc(100vh - 120px)">
    <div class="flex flex-col items-center w-full max-w-2xl">
      <div class="flex items-center gap-2 mb-3">
        <div class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
        <span class="text-sm text-fg-secondary">思考中</span>
      </div>
      <div ref="thinkingEl" class="w-full h-64 overflow-y-auto text-sm text-fg-dim leading-relaxed whitespace-pre-wrap scrollbar-hidden">{{ thinking }}</div>
    </div>
  </div>

  <!-- Split panel -->
  <div v-else-if="modelValue" class="flex gap-4" style="height: calc(100vh - 120px)">
    <!-- Left: markdown source -->
    <div class="w-1/2 flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white">
      <div class="flex items-center justify-between px-4 py-2.5 border-b border-border-subtle bg-bg-base/50">
        <span class="text-xs font-medium text-fg-dim">Markdown</span>
        <span v-if="status === 'completed'" class="text-[11px] text-accent/70">可编辑</span>
      </div>
      <textarea
        ref="textareaRef"
        :value="modelValue"
        @input="onInput"
        :readonly="status === 'running'"
        class="flex-1 w-full p-4 text-sm font-mono leading-relaxed resize-none focus:outline-none text-fg"
        :class="{ 'bg-gray-50': status === 'running' }"
        spellcheck="false"
      />
    </div>

    <!-- Right: rendered preview -->
    <div class="w-1/2 flex flex-col border border-border-subtle rounded-2xl overflow-hidden bg-white">
      <div class="px-4 py-2.5 border-b border-border-subtle bg-bg-base/50">
        <span class="text-xs font-medium text-fg-dim">预览</span>
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
