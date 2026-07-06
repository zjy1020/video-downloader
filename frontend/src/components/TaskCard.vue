<template>
  <div class="task-card" :class="statusClass" :data-task-id="task.task_id" @click="showDetail">
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

      <div v-if="task.error" class="card-error" :title="task.error">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ task.error }}
      </div>

      <div class="card-actions" @click.stop>
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

    <Transition name="modal">
      <div v-if="detailVisible" class="detail-overlay" @click.self="hideDetail">
        <div class="detail-modal" @click.stop>
          <button class="detail-close" @click="hideDetail">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>

          <div class="detail-media">
            <img v-if="thumbSrc" :src="thumbSrc" class="detail-img" />
            <div v-else class="detail-placeholder">
              <svg v-if="task.type === 'video'" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="23 7 16 12 23 17 23 7" />
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
              <svg v-else width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
            </div>
          </div>

          <div class="detail-body">
            <h2 class="detail-title">{{ task.title }}</h2>

            <div class="detail-row">
              <span class="detail-label">类型</span>
              <span class="detail-value">{{ task.type === 'video' ? '视频' : '图片' }}</span>
            </div>

            <div class="detail-row">
              <span class="detail-label">状态</span>
              <span class="detail-value">
                <span class="status-icon" :class="'icon-' + task.status" style="margin-right:4px">{{ statusIcon }}</span>
                {{ statusLabel }}
              </span>
            </div>

            <div v-if="task.status === 'downloading' || task.status === 'waiting'" class="detail-row">
              <span class="detail-label">进度</span>
              <span class="detail-value">{{ task.progress >= 0 ? task.progress + '%' : '未知' }}</span>
            </div>

            <div v-if="task.status === 'downloading' || task.status === 'waiting'" class="detail-progress">
              <div class="progress-bar">
                <div v-if="task.progress >= 0" class="progress-fill" :style="{ width: task.progress + '%' }"></div>
                <div v-else class="progress-indeterminate"></div>
              </div>
            </div>

            <div v-if="task.error" class="detail-row">
              <span class="detail-label">错误</span>
              <span class="detail-value detail-error">{{ task.error }}</span>
            </div>

            <div v-if="task.file_path" class="detail-row">
              <span class="detail-label">路径</span>
              <span class="detail-value detail-path" :title="task.file_path">{{ task.file_path }}</span>
            </div>

            <div class="detail-row">
              <span class="detail-label">ID</span>
              <span class="detail-value detail-mono">{{ task.task_id }}</span>
            </div>

            <div class="detail-actions">
              <button
                v-if="task.status === 'failed'"
                class="btn-icon btn-retry"
                @click="retry"
              >重试</button>
              <button
                v-if="task.status === 'success'"
                class="btn-icon btn-open"
                @click="openFolder"
              >打开文件夹</button>
              <button class="btn-icon btn-delete" @click="remove; hideDetail()">删除</button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const props = defineProps({
  task: { type: Object, required: true },
})

const emit = defineEmits(['retry', 'delete'])
const API_BASE = '/api'
const detailVisible = ref(false)

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

function showDetail() {
  detailVisible.value = true
}

function hideDetail() {
  detailVisible.value = false
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
  overflow: visible;
  min-height: 0;
  cursor: pointer;
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

/* ── Detail Modal ── */
.detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-modal {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  width: 480px;
  max-width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
  box-shadow: var(--shadow-lg);
  position: relative;
  display: flex;
  flex-direction: column;
}

.detail-close {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: var(--bg-card);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  transition: all 0.15s;
}
.detail-close:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
  border-color: var(--border-hover);
}

.detail-media {
  width: 100%;
  height: 220px;
  overflow: hidden;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
  background: var(--bg-hover);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-muted);
}

.detail-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.detail-placeholder svg {
  opacity: 0.3;
}

.detail-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  line-height: 1.45;
  word-break: break-all;
}

.detail-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.detail-label {
  flex-shrink: 0;
  width: 48px;
  font-size: 12px;
  color: var(--text-muted);
  padding-top: 1px;
}

.detail-value {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
}

.detail-error {
  color: var(--error);
}

.detail-path {
  font-size: 11px;
  color: var(--text-secondary);
  word-break: break-all;
  font-family: var(--font-mono);
}

.detail-mono {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-muted);
}

.detail-progress {
  margin: -4px 0;
}

.detail-actions {
  display: flex;
  gap: 8px;
  padding-top: 6px;
  border-top: 1px solid var(--border);
}

.modal-enter-active {
  transition: opacity 0.2s ease-out;
}
.modal-enter-active .detail-modal {
  animation: modal-pop 0.2s ease-out;
}
.modal-leave-active {
  transition: opacity 0.12s ease-in;
}
.modal-leave-active .detail-modal {
  animation: modal-pop 0.12s ease-in reverse;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

@keyframes modal-pop {
  from { transform: scale(0.92); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
</style>
