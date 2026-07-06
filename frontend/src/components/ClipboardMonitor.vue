<template>
  <Transition name="toast-slide">
    <div v-if="visible" class="clipboard-toast">
      <div class="toast-header">📋 检测到链接</div>
      <div class="toast-url">{{ truncateUrl(detectedUrl) }}</div>
      <div class="toast-actions">
        <button class="toast-btn toast-parse" @click="parse">解析</button>
        <button class="toast-btn toast-ignore" @click="visible = false">忽略</button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['parse'])

const visible = ref(false)
const detectedUrl = ref('')
const lastUrl = ref('')
let pollTimer = null
let isFocused = true
let clipboardAvailable = false

const URL_PATTERNS = [
  /douyin\.com/i,
  /iesdouyin\.com/i,
  /bilibili\.com/i,
  /b23\.tv/i,
]

function matchesPlatform(text) {
  return URL_PATTERNS.some(re => re.test(text))
}

function truncateUrl(url, max = 48) {
  if (!url) return ''
  if (url.length <= max) return url
  return url.slice(0, max - 3) + '...'
}

async function pollClipboard() {
  if (!clipboardAvailable || !isFocused) return
  try {
    const text = await navigator.clipboard.readText()
    if (!text || text === lastUrl.value) return
    if (matchesPlatform(text)) {
      detectedUrl.value = text
      lastUrl.value = text
      visible.value = true
    }
  } catch {
    // permission denied or empty clipboard — skip
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(pollClipboard, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function onVisibilityChange() {
  isFocused = document.visibilityState === 'visible'
  if (isFocused) {
    startPolling()
  } else {
    stopPolling()
  }
}

function parse() {
  const url = detectedUrl.value
  visible.value = false
  if (url) {
    emit('parse', url)
  }
}

onMounted(() => {
  clipboardAvailable = !!navigator.clipboard
  if (clipboardAvailable) {
    startPolling()
  }
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onUnmounted(() => {
  stopPolling()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<style scoped>
.clipboard-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  min-width: 280px;
  max-width: 360px;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast-header {
  font-size: 13px;
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.toast-url {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  word-break: break-all;
  line-height: 1.4;
  padding: 6px 8px;
  background: var(--bg-hover);
  border-radius: 6px;
}

.toast-actions {
  display: flex;
  gap: 8px;
  margin-top: 4px;
}

.toast-btn {
  flex: 1;
  padding: 8px 0;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.15s;
}

.toast-parse {
  background: var(--accent);
  color: #fff;
}

.toast-parse:hover {
  filter: brightness(1.15);
}

.toast-ignore {
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border);
}

.toast-ignore:hover {
  color: var(--text-secondary);
  border-color: var(--border-hover);
  background: var(--bg-hover);
}

.toast-slide-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-slide-leave-active {
  transition: all 0.2s ease-in;
}

.toast-slide-enter-from {
  opacity: 0;
  transform: translateX(40px);
}

.toast-slide-leave-to {
  opacity: 0;
  transform: translateX(40px);
}
</style>
