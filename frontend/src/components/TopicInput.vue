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
  <div class="flex items-center justify-center min-h-screen px-4 relative overflow-hidden">
    <!-- Background ambient orbs -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute top-[15%] -left-32 w-[480px] h-[480px] bg-accent/[0.04] rounded-full blur-[100px] animate-float"></div>
      <div class="absolute bottom-[10%] -right-24 w-[400px] h-[400px] bg-accent/[0.06] rounded-full blur-[80px] animate-float-delayed"></div>
      <div class="absolute top-[60%] left-[40%] w-[300px] h-[300px] bg-[#E8D5C4]/20 rounded-full blur-[90px] animate-float-slow"></div>
    </div>

    <div class="w-full max-w-2xl text-center relative z-10">
      <!-- Brand -->
      <div class="mb-12">
        <h1 class="text-5xl font-bold tracking-tight text-fg mb-4 font-display">
          ScriptPilot
        </h1>
        <div class="w-10 h-[3px] bg-gradient-to-r from-accent to-accent-light mx-auto mb-5 rounded-full"></div>
        <p class="text-fg-secondary text-base font-light tracking-wide">
          输入主题或思路片段，AI 为你生成完整的口播稿
        </p>
      </div>

      <!-- Input area -->
      <div
        class="relative rounded-2xl transition-all duration-500 ease-out"
        :class="isFocused
          ? 'bg-white shadow-[0_0_0_2px_rgba(199,88,50,0.18),0_12px_40px_rgba(199,88,50,0.07)]'
          : 'bg-white shadow-[0_0_0_1px_rgba(44,32,20,0.06),0_2px_12px_rgba(44,32,20,0.03)]'
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
          class="w-full bg-transparent text-fg placeholder-fg-dim px-6 pt-5 pb-16 text-base leading-relaxed resize-none focus:outline-none rounded-2xl"
        ></textarea>

        <!-- Submit button -->
        <div class="absolute bottom-4 right-4 flex items-center gap-3">
          <span class="text-[11px] text-fg-dim tracking-wide">Enter ↵</span>
          <button
            @click="handleSubmit"
            :disabled="!topic.trim()"
            class="px-6 py-2.5 bg-accent text-white text-sm font-semibold rounded-xl
                   hover:bg-accent-light disabled:opacity-20 disabled:cursor-not-allowed
                   transition-all duration-300 active:scale-95 shadow-sm hover:shadow-md hover:shadow-accent/15"
          >
            开始创作
          </button>
        </div>
      </div>

      <!-- Bottom hint -->
      <p class="mt-6 text-xs text-fg-dim/60 tracking-wide">
        由 AI 驱动 · 支持多种风格 · 一键生成
      </p>
    </div>
  </div>
</template>
