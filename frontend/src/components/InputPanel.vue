<template>
  <div class="input-panel">
    <div class="panel-header">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
      解析新链接
    </div>

    <div class="input-row">
      <input
        v-model="urlText"
        class="url-input"
        placeholder="粘贴抖音 / B站分享链接，按回车解析"
        @keyup.enter="doParse"
      />
      <button class="btn btn-primary" :disabled="parsing" @click="doParse">
        <span v-if="parsing" class="spinner"></span>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="9 18 15 12 9 6" />
        </svg>
        {{ parsing ? '解析中' : '解析' }}
      </button>
    </div>

    <Transition name="fade">
      <div v-if="parseHistory.length > 0 && !parseResult" class="parse-history">
        <div class="history-header">
          最近解析
          <button class="btn-text" @click="clearHistory">清除记录</button>
        </div>
        <div
          v-for="(item, i) in parseHistory"
          :key="i"
          class="history-item"
          @click="loadHistoryParse(item)"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="history-ico">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span class="history-url">{{ item.url }}</span>
          <span v-if="item.title" class="history-title">{{ item.title }}</span>
        </div>
      </div>
    </Transition>

    <Transition name="slide-up">
      <div v-if="parseResult" class="parse-result">
        <button class="btn-back" @click="backToInput">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          返回
        </button>

        <div v-if="parseResult.cover" class="cover-wrap" @click="previewImg = parseResult.cover">
          <div class="cover-grad"></div>
          <img :src="proxyUrl(parseResult.cover)" class="cover-img" />
        </div>

        <div class="result-header">
          <div class="result-title">{{ parseResult.title || '未命名' }}</div>
          <div class="result-meta">
            <span class="platform-tag">{{ platformLabel }}</span>
            <span class="count-tag">{{ parseResult.task_list.length }} 个资源</span>
            <span v-if="isBilibili && showQuality" class="quality-tag bili" :class="{ active: parseQuality !== 'normal' }">
              <select v-model="parseQuality" class="quality-select" @change="onQualityChange">
                <option v-for="q in biliQualities" :key="q.value" :value="q.value">{{ q.label }}</option>
              </select>
              <span class="quality-hint" title="列出的清晰度为可选上限，视频本身若不支持会自动降级到最高可用画质">ⓘ</span>
            </span>
          </div>
        </div>

        <div class="file-list">
          <div
            v-for="item in parseResult.task_list"
            :key="item.index"
            class="file-item"
            :class="{ selected: selected[item.index] }"
            @click="toggle(item.index)"
          >
            <div class="file-check">
              <div class="checkbox" :class="{ checked: selected[item.index] }">
                <svg v-if="selected[item.index]" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
            </div>
            <div class="file-icon">
              <template v-if="item.type === 'image' && item.download_url">
                <img :src="proxyUrl(item.download_url)" class="file-thumb" @click.prevent.stop="previewImg = item.download_url" />
              </template>
              <svg v-else-if="item.type === 'video'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="23 7 16 12 23 17 23 7" />
                <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <circle cx="8.5" cy="8.5" r="1.5" />
                <polyline points="21 15 16 10 5 21" />
              </svg>
            </div>
            <div class="file-info">
              <div class="file-name">{{ item.title }}</div>
              <div v-if="item.size" class="file-size">{{ formatSize(item.size) }}</div>
            </div>
          </div>
        </div>

        <div class="dl-options">
          <div class="dl-mode-group">
            <label class="dl-option" :class="{ active: dlMode === 'auto' }">
              <input type="radio" value="auto" v-model="dlMode" />
              <span>自动</span>
            </label>
            <label class="dl-option" :class="{ active: dlMode === 'sequential' }">
              <input type="radio" value="sequential" v-model="dlMode" />
              <span>单线程</span>
            </label>
            <label class="dl-option" :class="{ active: dlMode === 'parallel' }">
              <input type="radio" value="parallel" v-model="dlMode" />
              <span>多线程</span>
            </label>
          </div>
          <div v-if="dlMode === 'parallel'" class="dl-threads-group">
            <span class="dl-threads-label">线程数</span>
            <input type="number" v-model.number="dlThreads" min="2" max="16" class="dl-threads-input" />
          </div>
        </div>

        <button
          class="btn btn-accent btn-download"
          :disabled="selectedCount === 0 || downloading"
          @click="downloadSelected"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="7 10 12 15 17 10" />
            <line x1="12" y1="15" x2="12" y2="3" />
          </svg>
          {{ downloading ? '添加任务中...' : `下载选中 (${selectedCount})` }}
        </button>
      </div>
    </Transition>

    <div v-if="parseResult && parseResult.task_list.length === 0 && !error" class="empty-result">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" class="empty-ico">
        <circle cx="11" cy="11" r="8" />
        <path d="m21 21-4.3-4.3" />
      </svg>
      <span>未解析到可下载的资源</span>
    </div>

    <Transition name="fade">
      <div v-if="error" class="error-msg">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        {{ error }}
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="previewImg" class="preview-overlay" @click="previewImg = ''">
        <img :src="proxyUrl(previewImg)" class="preview-img" />
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'

const emit = defineEmits(['tasks-added'])
const API_BASE = '/api'

const urlText = ref('')
const parsing = ref(false)
const downloading = ref(false)
const parseResult = ref(null)
const error = ref('')
const previewImg = ref('')
const selected = ref({})
const dlMode = ref('auto')
const dlThreads = ref(4)
const parseQuality = ref('normal')
const biliQualities = [
  { value: '16', label: '360P' },
  { value: '32', label: '480P' },
  { value: '64', label: '720P' },
  { value: '80', label: '1080P' },
  { value: '112', label: '1080P+' },
  { value: '116', label: '1080P 60帧' },
  { value: '120', label: '4K' },
]
const parseHistory = ref(loadParseHistory())

const selectedCount = computed(() =>
  Object.values(selected.value).filter(Boolean).length
)

const platformLabel = computed(() => {
  if (!parseResult.value) return ''
  const map = { bilibili: 'B站', douyin: '抖音' }
  return map[parseResult.value.platform] || parseResult.value.platform
})

const isBilibili = computed(() => parseResult.value?.platform === 'bilibili')

const showQuality = computed(() => {
  return parseResult.value?.type === 'video'
})

async function onQualityChange() {
  if (!urlText.value) return
  await doParse()
}

function proxyUrl(url) {
  if (!url) return ''
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return `${API_BASE}/proxy/image?url=${encodeURIComponent(url)}`
  }
  return url
}

function formatSize(bytes) {
  if (!bytes) return ''
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) { size /= 1024; i++ }
  return size.toFixed(1) + ' ' + units[i]
}

function toggle(index) {
  selected.value[index] = !selected.value[index]
}

function loadParseHistory() {
  try { return JSON.parse(localStorage.getItem('vd_parse_history') || '[]') } catch { return [] }
}

function saveParseHistory(url, title) {
  const history = loadParseHistory()
  history.unshift({ url, title, time: Date.now() })
  if (history.length > 10) history.length = 10
  localStorage.setItem('vd_parse_history', JSON.stringify(history))
  parseHistory.value = history
}

function loadHistoryParse(item) {
  urlText.value = item.url
}

function backToInput() {
  parseResult.value = null
  error.value = ''
  selected.value = {}
  urlText.value = ''
}

function clearHistory() {
  localStorage.removeItem('vd_parse_history')
  parseHistory.value = []
}

async function doParse() {
  const text = urlText.value.trim()
  if (!text) return
  error.value = ''
  parseResult.value = null
  selected.value = {}
  parsing.value = true
  try {
    const qualityParam = parseQuality.value === 'normal' ? '' : parseQuality.value
    const res = await axios.post(`${API_BASE}/parse`, { url: text, quality: qualityParam })
    if (res.data.code === 200) {
      parseResult.value = res.data.data
      if (res.data.data.quality) {
        parseQuality.value = res.data.data.quality
      }
      saveParseHistory(text, res.data.data.title)
      for (const item of res.data.data.task_list) {
        selected.value[item.index] = true
      }
    } else {
      if (parseQuality.value !== 'normal') {
        parseQuality.value = 'normal'
        await doParse()
        return
      }
      error.value = res.data.msg
    }
  } catch (e) {
    error.value = '解析请求失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    parsing.value = false
  }
}

async function downloadSelected() {
  if (!parseResult.value || selectedCount.value === 0) return
  downloading.value = true
  const tasks = parseResult.value.task_list.filter((item) => selected.value[item.index])
  try {
    for (const item of tasks) {
      await axios.post(`${API_BASE}/download`, {
        url: item.download_url,
        title: item.title,
        type: item.type,
        cover: item.cover,
        mode: dlMode.value,
        threads: dlThreads.value,
        album_title: parseResult.value.title,
        index: item.index,
        total: parseResult.value.task_list.length,
      })
    }
    emit('tasks-added')
  } catch (e) {
    error.value = '添加下载任务失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    downloading.value = false
  }
}
</script>

<style scoped>
.input-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 8px;
}

.input-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
}

.url-input {
  flex: 1;
  height: 52px;
  padding: 0 18px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.url-input::placeholder {
  color: var(--text-dim);
}

.url-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-glow);
}

.btn {
  padding: 10px 18px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.btn:disabled { opacity: 0.45; cursor: not-allowed; }

.btn-primary {
  height: 52px;
  padding: 0 28px;
  background: var(--accent);
  color: #fff;
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  box-shadow: 0 2px 12px var(--accent-glow);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-primary:hover:not(:disabled) {
  box-shadow: 0 6px 24px var(--accent-glow);
  filter: brightness(1.15);
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.97);
  transition-duration: 0.08s;
}

.btn-accent {
  background: var(--accent);
  color: #fff;
  width: 100%;
  justify-content: center;
  padding: 14px;
  font-size: 15px;
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-sm);
  box-shadow: 0 2px 12px var(--accent-glow);
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.btn-accent:hover:not(:disabled) {
  box-shadow: 0 6px 24px var(--accent-glow);
  filter: brightness(1.15);
}

.btn-accent:active:not(:disabled) {
  transform: scale(0.97);
  transition-duration: 0.08s;
}

.btn-accent:active:not(:disabled) {
  transform: scale(0.97);
  transition-duration: 0.08s;
}

.btn-download { margin-top: 8px; }

.dl-options {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.dl-mode-group {
  display: flex;
  gap: 2px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 2px;
}

.dl-option {
  padding: 5px 12px;
  border-radius: 6px;
  font-size: 12px;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;
}

.dl-option input { display: none; }

.dl-option.active {
  background: var(--accent-glow);
  color: var(--accent);
  font-weight: 500;
}

.dl-option:not(.active):hover {
  color: var(--text-secondary);
}

.dl-threads-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.dl-threads-label {
  font-size: 12px;
  color: var(--text-muted);
}

.dl-threads-input {
  width: 56px;
  padding: 4px 8px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 12px;
  outline: none;
  text-align: center;
}

.dl-threads-input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px var(--accent-glow);
}

.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.btn-text {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 11px;
  cursor: pointer;
  padding: 2px 6px;
  border-radius: 4px;
  transition: color 0.15s;
}
.btn-text:hover { color: var(--error); }

.btn-back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  padding: 4px 8px;
  margin-bottom: 8px;
  border-radius: 6px;
  transition: all 0.15s;
  align-self: flex-start;
}

.btn-back:hover {
  color: var(--accent);
  background: var(--accent-glow);
}

.parse-result {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.cover-wrap {
  position: relative;
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: 10px;
  cursor: pointer;
  animation: cover-in 0.4s ease-out;
}

.cover-grad {
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 50%, rgba(0,0,0,0.4) 100%);
  z-index: 1;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.3s;
}

.cover-wrap:hover .cover-grad {
  opacity: 1;
}

.cover-wrap:hover .cover-img {
  transform: scale(1.05);
}

.cover-img {
  width: 100%;
  max-height: 140px;
  object-fit: cover;
  display: block;
  transition: transform 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes cover-in {
  from { opacity: 0; transform: scale(0.92); }
  60% { transform: scale(1.03); }
  to { opacity: 1; transform: scale(1); }
}

.result-header {
  margin-bottom: 12px;
}

.result-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
  margin-bottom: 6px;
}

.result-meta {
  display: flex;
  gap: 8px;
}

.platform-tag {
  background: var(--accent-glow);
  color: var(--accent);
  padding: 1px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.count-tag {
  color: var(--text-muted);
  font-size: 11px;
  padding: 1px 8px;
  background: var(--bg-input);
  border-radius: 4px;
}

.quality-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 4px;
  cursor: pointer;
  border: 1px solid var(--border);
  color: var(--text-muted);
  transition: all 0.15s;
  user-select: none;
  position: relative;
}

.quality-tag:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.quality-tag.active {
  background: var(--accent-glow);
  color: var(--accent);
  border-color: transparent;
}

.quality-tag.bili::after {
  content: '▾';
  margin-left: 2px;
  font-size: 10px;
}

.quality-select {
  background: transparent;
  color: inherit;
  font-size: 11px;
  cursor: pointer;
  outline: none;
  border: none;
  padding: 0 4px;
}

.quality-hint {
  font-size: 11px;
  cursor: help;
  opacity: 0.5;
  margin-left: 2px;
  transition: opacity 0.15s;
}

.quality-hint:hover {
  opacity: 1;
}

.file-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.file-item:hover {
  background: var(--bg-hover);
  border-color: var(--border);
}

.file-item.selected {
  border-color: var(--border-active);
  background: var(--accent-glow);
}

.file-check { flex-shrink: 0; }

.checkbox {
  width: 20px;
  height: 20px;
  border-radius: 5px;
  border: 2px solid var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.15s;
}

.checkbox.checked {
  background: var(--accent);
  border-color: var(--accent);
}

.file-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}

.file-thumb {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 4px;
  cursor: pointer;
}

.file-info { flex: 1; min-width: 0; }

.file-name {
  font-size: 13px;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 1px;
}

.parse-history { margin-bottom: 10px; }

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 12px;
  transition: background 0.15s;
}

.history-item:hover { background: var(--bg-hover); }

.history-ico { flex-shrink: 0; color: var(--text-muted); }

.history-url {
  color: var(--text-secondary);
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.history-title {
  color: var(--text-muted);
  font-size: 11px;
  max-width: 120px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-result {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--text-muted);
  font-size: 13px;
}

.empty-ico { opacity: 0.3; }

.error-msg {
  margin-top: 10px;
  padding: 8px 12px;
  background: var(--error-bg);
  border: 1px solid rgba(248, 113, 113, 0.25);
  border-radius: var(--radius-sm);
  color: var(--error);
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.preview-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.preview-img {
  max-width: 90%;
  max-height: 90%;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-up-enter-active { transition: all 0.25s ease-out; }
.slide-up-leave-active { transition: all 0.15s ease-in; }
.slide-up-enter-from { opacity: 0; transform: translateY(10px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
