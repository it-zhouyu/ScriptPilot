<script setup>
import { ref } from 'vue'
import SupportPanel from './SupportPanel.vue'

const props = defineProps({
  show: { type: Boolean, default: false },
})
const emit = defineEmits(['close'])

const text = ref('')
const images = ref([])
const submitting = ref(false)
const done = ref(false)

function onFileChange(e) {
  const files = Array.from(e.target.files || [])
  for (const file of files) {
    if (images.value.length >= 3) break
    const reader = new FileReader()
    reader.onload = (ev) => {
      images.value.push({ name: file.name, data: ev.target.result, file })
    }
    reader.readAsDataURL(file)
  }
  e.target.value = ''
}

function removeImage(idx) {
  images.value.splice(idx, 1)
}

async function submit() {
  if (!text.value.trim() && images.value.length === 0) return
  submitting.value = true
  try {
    const form = new FormData()
    form.append('text', text.value)
    for (const img of images.value) {
      form.append('images', img.file)
    }
    const resp = await fetch('/api/feedback', { method: 'POST', body: form })
    if (resp.ok) {
      done.value = true
    } else {
      alert('提交失败，请稍后重试')
    }
  } catch {
    alert('网络错误，请稍后重试')
  } finally {
    submitting.value = false
  }
}

function close() {
  text.value = ''
  images.value = []
  done.value = false
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/40" @click="close"></div>
        <div class="relative w-full max-w-4xl min-h-[520px] max-h-[90vh] flex flex-col bg-white rounded-xl shadow-2xl overflow-hidden animate-fade-in">
          <!-- Header -->
          <div class="flex items-center justify-between px-6 py-4 border-b border-border-subtle">
            <h3 class="text-base font-semibold text-fg">帮ScriptPilot变得更好</h3>
            <button @click="close" class="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-bg-base transition-colors text-fg-dim">
              <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <!-- Body -->
          <div class="flex-1 overflow-y-auto">
            <!-- Success state -->
            <div v-if="done" class="grid grid-cols-1 md:grid-cols-[0.9fr_1fr] divide-y md:divide-y-0 md:divide-x divide-border-subtle">
              <div class="px-6 py-10 text-center flex flex-col justify-center">
                <div class="w-14 h-14 mx-auto mb-4 rounded-full bg-green-50 flex items-center justify-center">
                  <svg class="w-7 h-7 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <p class="text-base text-fg font-semibold">感谢您的反馈！</p>
                <p class="text-sm text-fg-secondary mt-2 leading-relaxed">我们会认真对待每一条建议，也欢迎继续支持 ScriptPilot 的长期维护。</p>
              </div>
              <div class="px-6 py-5 bg-bg-base/35">
                <SupportPanel />
              </div>
            </div>

            <!-- Feedback + support -->
            <template v-else>
              <div class="grid grid-cols-1 md:grid-cols-[1fr_0.95fr] divide-y md:divide-y-0 md:divide-x divide-border-subtle">
                <div class="px-6 py-5">
                  <h4 class="text-sm font-semibold text-fg mb-1">意见反馈</h4>
                  <p class="text-xs text-fg-dim mb-3">遇到问题或有优化建议？请告诉我们</p>
                  <textarea
                    v-model="text"
                    placeholder="请描述您遇到的问题或建议..."
                    class="w-full h-32 p-3 text-sm leading-relaxed border border-border-subtle rounded-xl resize-none focus:outline-none focus:border-accent/40 transition-colors text-fg placeholder:text-fg-dim/50"
                  ></textarea>

                  <div class="mt-3">
                    <div class="flex flex-wrap gap-2">
                      <div v-for="(img, idx) in images" :key="idx" class="relative group w-20 h-20 rounded-lg overflow-hidden border border-border-subtle">
                        <img :src="img.data" class="w-full h-full object-cover" />
                        <button @click="removeImage(idx)" class="absolute top-0.5 right-0.5 w-5 h-5 bg-black/50 rounded-full flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          <svg class="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                      <label v-if="images.length < 3" class="w-20 h-20 rounded-lg border-2 border-dashed border-border-subtle flex flex-col items-center justify-center cursor-pointer hover:border-accent/30 transition-colors">
                        <svg class="w-5 h-5 text-fg-dim" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
                        </svg>
                        <span class="text-[10px] text-fg-dim mt-1">添加图片</span>
                        <input type="file" accept="image/*" multiple class="hidden" @change="onFileChange" />
                      </label>
                    </div>
                  </div>
                </div>

                <div class="px-6 py-5 bg-bg-base/35">
                  <SupportPanel />
                </div>
              </div>
            </template>
          </div>

          <!-- Footer -->
          <div v-if="!done" class="px-6 py-4 border-t border-border-subtle flex justify-end gap-3">
            <button @click="close" class="px-5 py-2 text-sm text-fg-dim rounded-xl hover:bg-bg-base transition-colors">
              取消
            </button>
            <button
              @click="submit"
              :disabled="submitting || (!text.trim() && images.length === 0)"
              class="px-6 py-2 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ submitting ? '提交中...' : '提交反馈' }}
            </button>
          </div>
          <div v-else class="px-6 py-4 border-t border-border-subtle flex justify-end">
            <button @click="close" class="px-6 py-2 bg-accent text-white text-sm font-medium rounded-xl hover:bg-accent-light transition-all">
              关闭
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
