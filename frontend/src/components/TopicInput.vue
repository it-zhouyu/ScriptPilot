<script setup>
import { ref, computed } from 'vue'

const emit = defineEmits(['submit', 'switch-mode'])

const topic = ref('')
const isFocused = ref(false)
const textareaRef = ref(null)
const isAgentMode = ref(false)
const productFlowHint = computed(() =>
  isAgentMode.value
    ? '与 AI Agent 对话，智能完成创作全流程'
    : '选方向 · 定风格 · 生成可直接录制的口播稿'
)
const examples = [
  '普通人如何开始做短视频',
  'AI 编程工具如何改变独立开发者工作流',
  '职场新人如何用 AI 提升效率',
]

function handleSubmit() {
  if (topic.value.trim()) {
    if (isAgentMode.value) {
      emit('switch-mode', 'agent', topic.value.trim())
    } else {
      emit('submit', topic.value.trim())
    }
  }
}

function useExample(text) {
  topic.value = text
  textareaRef.value?.focus()
}

function toggleMode() {
  isAgentMode.value = !isAgentMode.value
}
</script>

<template>
  <div class="flex items-center justify-center min-h-screen px-4 relative overflow-hidden bg-[radial-gradient(circle_at_top,#fff_0,#f9f6f2_48%,#f3ede7_100%)]">
    <div class="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/25 to-transparent"></div>

    <div class="w-full max-w-3xl text-center relative z-10">
      <!-- Brand -->
      <div class="mb-10">
        <h1 class="text-5xl font-bold tracking-tight text-fg mb-4 font-display">
          ScriptPilot
        </h1>
        <div class="w-10 h-[3px] bg-gradient-to-r from-accent to-accent-light mx-auto mb-5 rounded-full"></div>
        <p class="text-fg-secondary text-base font-light tracking-wide">
          输入一个主题，AI 帮你确定创作方向、口播风格和完整稿件
        </p>
      </div>

      <!-- Input area -->
      <div
        class="relative rounded-lg transition-all duration-300 ease-out"
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
          class="w-full bg-transparent text-fg placeholder-fg-dim px-6 pt-5 pb-14 text-base leading-relaxed resize-none focus:outline-none rounded-lg"
        ></textarea>

        <!-- Bottom bar -->
        <div class="absolute bottom-3 inset-x-4 flex items-center justify-between">
          <!-- Left: Agent toggle -->
          <label class="flex items-center gap-2 cursor-pointer select-none">
            <button
              @click="toggleMode"
              role="switch"
              :aria-checked="isAgentMode"
              class="relative inline-flex h-[22px] w-[38px] items-center rounded-full transition-colors duration-200 focus:outline-none"
              :class="isAgentMode ? 'bg-accent' : 'bg-gray-200'"
            >
              <span
                class="inline-block h-4 w-4 rounded-full bg-white shadow-sm transition-transform duration-200"
                :class="isAgentMode ? 'translate-x-[18px]' : 'translate-x-[2px]'"
              ></span>
            </button>
            <span class="text-xs" :class="isAgentMode ? 'text-accent font-medium' : 'text-fg-dim'">Agent</span>
          </label>
          <!-- Right: Submit -->
          <button
            @click="handleSubmit"
            :disabled="!topic.trim()"
            class="flex items-center gap-1.5 px-5 py-2 bg-accent text-white text-sm font-semibold rounded-lg
                   hover:bg-accent-light disabled:opacity-20 disabled:cursor-not-allowed
                   transition-all duration-200 active:scale-95 shadow-sm hover:shadow-md hover:shadow-accent/15"
          >
            开始创作
            <kbd class="text-[10px] opacity-60 font-normal">↵</kbd>
          </button>
        </div>
      </div>

      <div class="mt-5 flex flex-wrap items-center justify-center gap-2">
        <button
          v-for="example in examples"
          :key="example"
          @click="useExample(example)"
          class="px-3 py-1.5 text-xs text-fg-secondary border border-border-subtle rounded-lg bg-white/60 hover:bg-white hover:border-accent/30 hover:text-accent transition-colors"
        >
          {{ example }}
        </button>
      </div>

      <!-- Bottom hint -->
      <p class="mt-6 text-xs text-fg-dim/60 tracking-wide">
        {{ productFlowHint }}
      </p>
    </div>
  </div>
</template>
