<script setup>
import ThinkingIndicator from './ThinkingIndicator.vue'
import '../assets/prose.css'

const props = defineProps({
  stageKey: { type: String, required: true },
  title: { type: String, required: true },
  content: { type: String, default: '' },
  thinking: { type: String, default: '' },
  status: { type: String, default: 'waiting' },
})
</script>

<template>
  <div class="stage-block">
    <ThinkingIndicator v-if="status === 'running' && !content" :thinking="thinking" />
    <div v-if="content" class="prose-content" v-html="content"></div>
  </div>
</template>

<style scoped>
.stage-block {
  font-size: 15px;
  line-height: 1.85;
}
</style>
