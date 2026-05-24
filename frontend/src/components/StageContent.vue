<script setup>
import { ref, watch, nextTick } from 'vue'
import '../assets/prose.css'

const props = defineProps({
  stageKey: { type: String, required: true },
  title: { type: String, required: true },
  content: { type: String, default: '' },
  thinking: { type: String, default: '' },
  status: { type: String, default: 'waiting' },
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
  <div class="stage-block">
    <!-- Thinking phase: fixed centered container -->
    <div v-if="status === 'running' && !content" class="flex items-center justify-center" style="height: calc(100vh - 120px)">
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

    <!-- Content area -->
    <div v-if="content" class="prose-content" v-html="content"></div>
  </div>
</template>

<style scoped>
.stage-block {
  font-size: 15px;
  line-height: 1.85;
}
.typing-cursor::after {
  content: '▌';
  animation: blink 1s step-end infinite;
  color: var(--accent, #5E6AD2);
  margin-left: 2px;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>

