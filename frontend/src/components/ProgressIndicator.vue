<script setup>
import { computed } from 'vue'

const props = defineProps({
  phase: { type: String, required: true },
  currentStage: { type: String, default: null },
})

const steps = [
  { key: 'input', label: '输入主题' },
  { key: 'direction', label: '选择方向' },
  { key: 'generate', label: '内容生成' },
  { key: 'done', label: '完成' },
]

const stageLabels = {
  research: '资料收集',
  style: '口播风格',
  outline: '口播大纲',
  script: '口播稿',
  content: '自媒体文章',
}

const phaseToStepIndex = computed(() => {
  const map = {
    input: 0,
    analyzing: 1,
    'select-direction': 1,
    generating: 2,
    done: 3,
  }
  return map[props.phase] ?? 0
})

const getStepStatus = (index) => {
  if (index < phaseToStepIndex.value) return 'completed'
  if (index === phaseToStepIndex.value) return 'active'
  return 'pending'
}
</script>

<template>
  <div class="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-border-subtle">
    <div class="max-w-3xl mx-auto px-4 py-3">
      <div class="flex items-center gap-1">
        <template v-for="(step, i) in steps" :key="step.key">
          <!-- Step dot and label -->
          <div class="flex items-center gap-2">
            <div
              class="w-2 h-2 rounded-full transition-all duration-300"
              :class="{
                'bg-green-500': getStepStatus(i) === 'completed',
                'bg-accent shadow-[0_0_8px_rgba(94,106,210,0.5)] animate-pulse': getStepStatus(i) === 'active',
                'bg-fg-dim': getStepStatus(i) === 'pending',
              }"
            />
            <span
              class="text-xs font-medium transition-colors duration-300 whitespace-nowrap"
              :class="{
                'text-fg': getStepStatus(i) === 'completed' || getStepStatus(i) === 'active',
                'text-fg-dim': getStepStatus(i) === 'pending',
              }"
            >
              {{ step.label }}
              <span v-if="step.key === 'generate' && currentStage && getStepStatus(i) === 'active'" class="text-accent-light ml-1">
                · {{ stageLabels[currentStage] }}
              </span>
            </span>
          </div>
          <!-- Connector line -->
          <div
            v-if="i < steps.length - 1"
            class="flex-1 h-px mx-2 transition-colors duration-300"
            :class="getStepStatus(i) === 'completed' ? 'bg-green-500/40' : 'bg-border-subtle'"
          />
        </template>
      </div>
    </div>
  </div>
</template>
