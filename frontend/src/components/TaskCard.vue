<template>
  <div class="task-card" :class="statusClass">
    <div class="card-left">
      <div v-if="task.cover" class="card-thumb">
        <img :src="proxyUrl(task.cover)" />
      </div>
      <div v-else class="card-thumb card-thumb-placeholder">
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
      <div class="card-title-row">
        <span class="card-title" :title="task.title">{{ task.title }}</span>
        <span class="status-badge" :class="'status-' + task.status">
          <span class="status-dot" :class="'dot-' + task.status"></span>
          {{ statusLabel }}
        </span>
      </div>

      <div class="card-progress-area">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: task.progress + '%' }"></div>
        </div>
        <span class="progress-text">{{ task.progress }}%</span>
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
          @click="openFile"
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
            <polyline points="15 3 21 3 21 9" />
            <line x1="10" y1="14" x2="21" y2="3" />
          </svg>
          打开文件
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
import { computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['retry', 'delete'])
const API_BASE = '/api'

const statusLabel = computed(() => {
  const map = { waiting: '等待中', downloading: '下载中', success: '已完成', failed: '失败' }
  return map[props.task.status] || props.task.status
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

function openFile() {
  if (props.task.file_path) {
    window.open('file:///' + props.task.file_path.replace(/\\/g, '/'))
  }
}
</script>

<style scoped>
.task-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
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
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

.card-left { flex-shrink: 0; }

.card-thumb {
  width: 72px;
  height: 48px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: var(--bg-input);
}

.card-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.card-thumb-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.card-body {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-badge {
  flex-shrink: 0;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.dot-waiting { background: var(--warning); }
.dot-downloading { background: var(--accent); animation: pulse 1.2s ease-in-out infinite; }
.dot-success { background: var(--success); }
.dot-failed { background: var(--error); }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.status-waiting { background: var(--warning-bg); color: var(--warning); }
.status-downloading { background: var(--accent-glow); color: var(--accent); }
.status-success { background: var(--success-bg); color: var(--success); }
.status-failed { background: var(--error-bg); color: var(--error); }

.card-progress-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 5px;
  background: var(--progress-bg);
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.card-downloading .progress-fill {
  background: linear-gradient(90deg, var(--accent), #7c3aed);
  background-size: 200% 100%;
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
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
  font-weight: 500;
}

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

.card-actions {
  display: flex;
  gap: 4px;
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 1px solid var(--border);
  border-radius: 6px;
  font-size: 11px;
  cursor: pointer;
  background: transparent;
  color: var(--text-secondary);
  transition: all 0.15s;
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
</style>
