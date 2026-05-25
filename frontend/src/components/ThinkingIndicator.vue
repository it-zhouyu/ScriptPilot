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
      <div class="flex items-center gap-3 mb-4">
        <div class="flex gap-1.5">
          <span class="w-2 h-2 bg-accent/60 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
          <span class="w-2 h-2 bg-accent/80 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
          <span class="w-2 h-2 bg-accent rounded-full animate-bounce" style="animation-delay: 300ms"></span>
        </div>
        <span class="text-sm text-fg-secondary font-medium">{{ label }}</span>
      </div>
      <div ref="thinkingEl" class="w-full h-64 overflow-y-auto text-sm text-fg-dim/70 leading-relaxed whitespace-pre-wrap scrollbar-hidden font-light">{{ thinking }}</div>
    </div>
  </div>
</template>
