<script setup>
import { ref } from 'vue'

const emit = defineEmits(['submit'])

const topic = ref('')
const isFocused = ref(false)
const textareaRef = ref(null)

function handleSubmit() {
  if (topic.value.trim()) {
    emit('submit', topic.value.trim())
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen px-4">
    <div class="w-full max-w-2xl text-center">
      <!-- Brand -->
      <div class="mb-10">
        <h1 class="text-3xl font-bold tracking-tight text-fg mb-3">
          ScriptPilot
        </h1>
        <p class="text-fg-secondary text-base">
          输入主题或思路片段，AI 为你生成完整的口播稿
        </p>
      </div>

      <!-- Input area -->
      <div
        class="relative rounded-2xl transition-all duration-300"
        :class="isFocused
          ? 'bg-white shadow-[0_0_0_2px_rgba(94,106,210,0.25),0_4px_16px_rgba(94,106,210,0.08)]'
          : 'bg-white shadow-[0_0_0_1px_#E2E8F0,0_1px_3px_rgba(0,0,0,0.04)]'
        "
      >
        <textarea
          ref="textareaRef"
          v-model="topic"
          @focus="isFocused = true"
          @blur="isFocused = false"
          @keydown.enter.exact.prevent="handleSubmit"
          placeholder="请输入你想要创作的主题"
          rows="3"
          class="w-full bg-transparent text-fg placeholder-fg-dim px-5 pt-4 pb-14 text-base leading-relaxed resize-none focus:outline-none rounded-2xl"
        ></textarea>

        <!-- Submit button -->
        <div class="absolute bottom-3 right-3 flex items-center gap-2">
          <span class="text-xs text-fg-dim mr-1">Enter 发送</span>
          <button
            @click="handleSubmit"
            :disabled="!topic.trim()"
            class="px-5 py-2 bg-accent text-white text-sm font-medium rounded-xl
                   hover:bg-accent-light disabled:opacity-30 disabled:cursor-not-allowed
                   transition-all duration-200 active:scale-95"
          >
            开始创作
          </button>
        </div>
      </div>

    </div>
  </div>
</template>
