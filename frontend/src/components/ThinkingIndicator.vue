<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  label: { type: String, default: '思考中' },
  thinking: { type: String, default: '' },
})

const thinkingEl = ref(null)

watch(() => props.thinking, () => {
  if (thinkingEl.value) {
    nextTick(() => {
      thinkingEl.value.scrollTop = thinkingEl.value.scrollHeight
    })
  }
})
</script>

<template>
  <div class="flex items-center justify-center" style="height: calc(100vh - 120px)">
    <div class="flex flex-col items-center w-full max-w-2xl">
      <div class="flex items-center gap-2 mb-3">
        <div class="flex gap-1">
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-1.5 h-1.5 bg-accent rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
        <span class="text-sm text-fg-secondary">{{ label }}</span>
      </div>
      <div ref="thinkingEl" class="w-full h-64 overflow-y-auto text-sm text-fg-dim leading-relaxed whitespace-pre-wrap scrollbar-hidden">{{ thinking }}</div>
    </div>
  </div>
</template>
