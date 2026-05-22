<template>
  <div class="flex gap-3">
    <input
      v-model="topic"
      @keyup.enter="handleGenerate"
      :disabled="loading"
      type="text"
      placeholder="输入主题，例如：人工智能在教育领域的应用"
      class="flex-1 px-4 py-3 border border-gray-300 rounded-lg text-base focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100 disabled:text-gray-400"
    />
    <button
      @click="handleGenerate"
      :disabled="loading || !topic.trim()"
      class="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
    >
      <span v-if="loading" class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
      {{ loading ? '生成中...' : '开始生成' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  loading: Boolean,
})

const emit = defineEmits(['generate'])

const topic = ref('')

function handleGenerate() {
  if (topic.value.trim() && !props.loading) {
    emit('generate', topic.value.trim())
  }
}

function reset() {
  topic.value = ''
}

defineExpose({ reset })
</script>
