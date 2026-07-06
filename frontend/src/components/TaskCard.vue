<template>
  <div class="task-card" :class="statusClass" :data-task-id="task.task_id">
    <div class="card-thumb">
      <img v-if="thumbSrc" :src="thumbSrc" />
      <div v-else class="thumb-placeholder">
        <svg v-if="task.type === 'video'" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
        </svg>
        <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
          <circle cx="8.5" cy="8.5" r="1.5" />
          <polyline points="21 15 16 10 5 21" />
        </svg>
      </div>
    </div>

    <div class="card-body">
      <div class="card-top">
        <span class="card-title" :title="task.title">{{ task.title }}</span>
        <span class="status-icon" :class="'icon-' + task.status">{{ statusIcon }}</span>
      </div>

      <div v-if="task.status === 'downloading' || task.status === 'waiting'" class="card-progress-area">
        <div class="progress-bar">
          <div v-if="task.progress >= 0" class="progress-fill" :style="{ width: task.progress + '%' }"></div>
          <div v-else class="progress-indeterminate"></div>
        </div>
        <span class="progress-text">{{ task.progress >= 0 ? task.progress + '%' : '...' }}</span>
      </div>

      <div v-if="task.status === 'downloading' && task.downloaded_bytes > 0" class="card-speed-row">
        <span class="speed-val">{{ speedText }}</span>
        <span class="speed-sep">·</span>
        <span class="speed-progress">{{ formatBytes(task.downloaded_bytes) }} / {{ formatBytes(task.total_bytes) }}</span>
        <span v-if="etaText" class="speed-eta">剩余 {{ etaText }}</span>
      </div>

      <div v-if="task.status === 'success' && task.finished_at && task.started_at" class="card-complete-row">
        <span class="complete-duration">耗时 {{ durationText }}</span>
        <span class="speed-sep">·</span>
        <span class="complete-speed">平均 {{ avgSpeedText }}</span>
      </div>

      <div v-if="task.error" class="card-error" :title="task.error">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ task.error }}
      </div>

      <div class="card-actions">
        <button
          v-if="task.status === 'failed'"
          class="btn-icon btn-retry"
          @click="retry"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          重试
        </button>
        <button
          v-if="task.status === 'success'"
          class="btn-icon btn-open"
          @click="openFolder"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
          </svg>
          打开文件夹
        </button>
        <button
          v-if="task.status === 'waiting' || task.status === 'failed'"
          class="btn-icon btn-delete"
          @click="remove"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
          删除
        </button>
        <button
          v-else-if="task.status === 'success'"
          class="btn-icon btn-delete"
          @click="remove"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
          删除
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['retry', 'delete'])
const API_BASE = '/api'

const speedBytesPerSec = ref(0)
const lastBytes = ref(0)
const lastTime = ref(0)

watch(() => props.task.downloaded_bytes, (val) => {
  if (!val || val <= 0) { speedBytesPerSec.value = 0; return }
  const now = Date.now()
  if (lastTime.value && lastBytes.value > 0 && val > lastBytes.value) {
    const delta = val - lastBytes.value
    const dt = (now - lastTime.value) / 1000
    if (dt > 0) speedBytesPerSec.value = delta / dt
  }
  lastBytes.value = val
  lastTime.value = now
})

const speedText = computed(() => {
  if (!speedBytesPerSec.value) return ''
  return formatSpeed(speedBytesPerSec.value)
})

const etaText = computed(() => {
  if (!speedBytesPerSec.value || !props.task.total_bytes) return ''
  const remaining = props.task.total_bytes - props.task.downloaded_bytes
  if (remaining <= 0) return ''
  const secs = remaining / speedBytesPerSec.value
  return formatDuration(secs)
})

const durationText = computed(() => {
  const s = props.task.started_at, f = props.task.finished_at
  if (!s || !f) return ''
  return formatDuration(f - s)
})

const avgSpeedText = computed(() => {
  const s = props.task.started_at, f = props.task.finished_at
  if (!s || !f || !props.task.total_bytes) return ''
  const dt = f - s
  if (dt <= 0) return ''
  return formatSpeed(props.task.total_bytes / dt)
})

function formatSpeed(bps) {
  if (bps <= 0) return ''
  if (bps >= 1048576) return (bps / 1048576).toFixed(1) + ' MB/s'
  return (bps / 1024).toFixed(0) + ' KB/s'
}

function formatBytes(bytes) {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0; let v = bytes
  while (v >= 1024 && i < units.length - 1) { v /= 1024; i++ }
  return v.toFixed(i > 0 ? 1 : 0) + ' ' + units[i]
}

function formatDuration(secs) {
  if (secs < 0) secs = 0
  if (secs < 60) return Math.round(secs) + '秒'
  if (secs < 3600) return Math.floor(secs / 60) + '分' + Math.round(secs % 60) + '秒'
  return Math.floor(secs / 3600) + '时' + Math.floor((secs % 3600) / 60) + '分'
}

const thumbSrc = computed(() => {
  if (props.task.type === 'image' && props.task.url) {
    return proxyUrl(props.task.url)
  }
  if (props.task.cover) {
    return proxyUrl(props.task.cover)
  }
  return ''
})

const statusIcon = computed(() => {
  const map = {
    waiting: '○',
    downloading: '⬇',
    success: '✓',
    failed: '✖',
  }
  return map[props.task.status] || ''
})

const statusClass = computed(() => 'card-' + props.task.status)

function proxyUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return `${API_BASE}/proxy/image?url=${encodeURIComponent(url)}`
  }
  return url
}

async function retry() {
  try {
    await axios.post(`${API_BASE}/download/retry`, { task_id: props.task.task_id })
    emit('retry', props.task.task_id)
  } catch (e) { console.error('重试失败', e) }
}

function remove() {
  axios.delete(`${API_BASE}/download/${props.task.task_id}`).catch(() => {})
  emit('delete', props.task.task_id)
}

async function openFolder() {
  try {
    const res = await axios.post(`${API_BASE}/download/open-folder/${props.task.task_id}`)
    if (res.data.code !== 200) {
      console.error('打开文件夹失败:', res.data.msg)
    }
  } catch (e) {
    console.error('打开文件夹失败', e)
  }
}
</script>

<style scoped>
.task-card {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-height: 0;
}

.task-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  transition: background 0.3s;
}

.card-success::before { background: var(--success); }
.card-downloading::before { background: var(--accent); }
.card-failed::before { background: var(--error); }
.card-waiting::before { background: var(--warning); }

.task-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0,0,0,0.25);
}

/* ── Thumbnail ── */
.card-thumb {
  width: 56px;
  height: 56px;
  border-radius: 10px;
  overflow: hidden;
  background: var(--bg-hover);
  flex-shrink: 0;
  align-self: flex-start;
}

.card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumb-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

/* ── Body ── */
.card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.card-top {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.card-title {
  flex: 1;
  font-size: 13px;
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.status-icon {
  flex-shrink: 0;
  font-size: 15px;
  line-height: 1;
  margin-top: 1px;
}

.icon-waiting { color: var(--warning); }
.icon-downloading { color: var(--accent); }
.icon-success { color: var(--success); }
.icon-failed { color: var(--error); }

/* ── Progress ── */
.card-progress-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--progress-bg);
  border-radius: 2px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.card-downloading .progress-fill {
  background: var(--accent);
  transition: width 0.3s ease;
}

.progress-indeterminate {
  height: 100%;
  width: 35%;
  border-radius: 999px;
  background: var(--accent);
  animation: indeterminate 0.8s ease-in-out infinite;
}

@keyframes indeterminate {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.card-success .progress-fill {
  background: var(--success);
  width: 100% !important;
}

.progress-text {
  font-size: 12px;
  color: var(--text-secondary);
  min-width: 36px;
  text-align: right;
  font-family: var(--font-mono);
  font-weight: var(--font-weight-medium);
}

/* ── Speed / ETA ── */
.card-speed-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.speed-val {
  color: var(--accent);
  font-weight: var(--font-weight-medium);
}

.speed-sep {
  opacity: 0.3;
}

.speed-eta {
  margin-left: auto;
  color: var(--text-secondary);
}

/* ── Complete info ── */
.card-complete-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.complete-duration, .complete-speed {
  color: var(--text-secondary);
}

/* ── Error ── */
.card-error {
  font-size: 11px;
  color: var(--error);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* ── Actions ── */
.card-actions {
  display: flex;
  gap: 6px;
  flex-shrink: 0;
  margin-top: 2px;
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 11px;
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  background: transparent;
  color: var(--text-secondary);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-icon:hover {
  border-color: var(--border-hover);
  background: var(--bg-hover);
  color: var(--text-primary);
}

.btn-retry {
  color: var(--warning);
  border-color: rgba(251, 191, 36, 0.25);
}
.btn-retry:hover {
  background: var(--warning-bg);
  border-color: rgba(251, 191, 36, 0.4);
}

.btn-open {
  color: var(--success);
  border-color: rgba(52, 211, 153, 0.25);
}
.btn-open:hover {
  background: var(--success-bg);
  border-color: rgba(52, 211, 153, 0.4);
}

.btn-delete {
  color: var(--text-muted);
  border-color: transparent;
}
.btn-delete:hover {
  color: var(--error);
  background: var(--error-bg);
  border-color: rgba(248, 113, 113, 0.25);
}

/* ── Success bounce animation ── */
.card-success .status-icon {
  animation: bounce-in 0.4s cubic-bezier(0.68, -0.15, 0.27, 1.15);
}

@keyframes bounce-in {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.3); }
  100% { transform: scale(1); opacity: 1; }
}
</style>
