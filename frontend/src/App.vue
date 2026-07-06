<template>
  <div class="app" :class="theme">
    <video autoplay muted loop playsinline class="bg-video" ref="videoRef">
      <source src="/bg.mp4" type="video/mp4" />
    </video>
    <div class="bg-vignette"></div>

    <Transition name="landing-leave">
      <div v-if="!entered" class="landing">
        <div class="landing-content">
          <div class="landing-logo">
            <img src="/logo.png" alt="logo" class="landing-logo-img" />
          </div>
          <h1 class="landing-title">解析</h1>
          <p class="landing-desc">B站 / 抖音视频 & 图文链接解析下载</p>
          <button class="landing-btn" @click="enterApp">
            进入
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </div>
    </Transition>

    <Transition name="app-enter">
      <div v-if="entered" class="app-inner">
        <ClipboardMonitor @parse="onClipboardParse" />
        <Transition name="notif">
          <div v-if="completedNotif" class="completed-notif" @click="completedNotif = null">
            <div class="notif-icon">✔</div>
            <div class="notif-body">
              <div class="notif-title">下载完成</div>
              <div class="notif-file">{{ completedNotif.title }}</div>
            </div>
          </div>
        </Transition>
        <header class="app-header">
          <div class="header-left">
            <div class="logo">
              <img src="/logo.png" alt="logo" class="logo-img" />
            </div>
            <h1 class="app-title">解析</h1>
            <span class="app-badge">V2</span>
          </div>
          <div class="header-right">
            <button class="btn-theme" @click="toggleTheme" :title="theme === 'dark' ? '切换到浅色模式' : '切换到深色模式'">
              <svg v-if="theme === 'dark'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
              </svg>
            </button>
            <span class="dir-label">下载目录</span>
            <code class="dir-path" :title="downloadDir">{{ downloadDir }}</code>
            <button class="btn-ghost" @click="changeDir">更改</button>
          </div>
        </header>

        <main class="app-main">
          <section class="panel panel-left">
            <InputPanel :clipboard-url="urlInput" @tasks-added="onTasksAdded" />
          </section>
          <section class="panel panel-right">
            <DownloadStats :stats="stats" />
            <TaskList
              :tasks="tasks"
              @retry="refreshTasks"
              @delete="refreshTasks"
            />
          </section>
        </main>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import InputPanel from './components/InputPanel.vue'
import TaskList from './components/TaskList.vue'
import ClipboardMonitor from './components/ClipboardMonitor.vue'
import DownloadStats from './components/DownloadStats.vue'
import { useStats } from './composables/useStats.js'

const API_BASE = '/api'
const downloadDir = ref('')
const tasks = ref([])
const entered = ref(false)
const theme = ref('dark')
const videoRef = ref(null)
const urlInput = ref('')
const inputPanelKey = ref(0)
const stats = useStats()
let pollTimer = null
let prevTasks = {} // keyed by task_id, for detecting new completions
const completedNotif = ref(null) // { title, platform }

function loadTheme() {
  try {
    const saved = localStorage.getItem('vd_theme')
    if (saved === 'light' || saved === 'dark') theme.value = saved
  } catch { /* noop */ }
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  try { localStorage.setItem('vd_theme', theme.value) } catch { /* noop */ }
}

function enterApp() {
  entered.value = true
}

async function getDownloadDir() {
  const res = await axios.get(`${API_BASE}/download_dir`)
  downloadDir.value = res.data.path
}

function setDir(path) {
  if (!path) return
  axios.post(`${API_BASE}/set_download_dir`, { path }).then(() => {
    downloadDir.value = path
  }).catch((e) => {
    alert('设置目录失败: ' + (e.response?.data?.detail || e.message))
  })
}

async function changeDir() {
  const path = prompt('输入下载目录路径：', downloadDir.value)
  if (path) setDir(path.trim())
}

function saveTasksToCache(data) {
  try {
    localStorage.setItem('vd_tasks_cache', JSON.stringify(data))
  } catch { /* noop */ }
}

function loadTasksFromCache() {
  try {
    const cached = localStorage.getItem('vd_tasks_cache')
    if (cached) {
      tasks.value = JSON.parse(cached).filter(
        (t) => t.status === 'success' || t.status === 'failed'
      )
    }
  } catch { /* noop */ }
}

function onClipboardParse(url) {
  urlInput.value = url
  setTimeout(() => { urlInput.value = '' }, 500)
}

async function fetchTasks() {
  try {
    const res = await axios.get(`${API_BASE}/tasks`)
    const data = res.data.data
    // detect new completions
    for (const t of data) {
      const prev = prevTasks[t.task_id]
      if (t.status === 'success' && prev && prev.status !== 'success') {
        completedNotif.value = { title: t.title, platform: t.type === 'video' ? 'bilibili' : 'douyin' }
        stats.recordDownload(t.type === 'video' ? 'bilibili' : 'douyin', t.total_bytes)
        setTimeout(() => { completedNotif.value = null }, 5000)
      }
    }
    prevTasks = {}
    for (const t of data) prevTasks[t.task_id] = { status: t.status }
    tasks.value = data
    saveTasksToCache(data)
  } catch {
    loadTasksFromCache()
  }
}

function startPolling() {
  stopPolling()
  pollTimer = setInterval(fetchTasks, 800)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

function onTasksAdded() {
  fetchTasks()
  startPolling()
}

function refreshTasks() {
  fetchTasks()
}

onMounted(async () => {
  loadTheme()
  await getDownloadDir()
  await fetchTasks()
})

onUnmounted(stopPolling)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --bg-app: #08080c;
  --bg-surface: rgba(255, 255, 255, 0.04);
  --bg-card: rgba(255, 255, 255, 0.05);
  --bg-input: transparent;
  --bg-hover: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.07);
  --border-hover: rgba(255, 255, 255, 0.14);
  --border-active: rgba(91, 154, 255, 0.5);
  --accent: #5b9aff;
  --accent-hover: #7bb0ff;
  --accent-glow: rgba(91, 154, 255, 0.2);
  --text-primary: #e8ecf4;
  --text-secondary: #8b95a8;
  --text-muted: #5a6377;
  --text-dim: rgba(138, 149, 168, 0.45);
  --success: #34d399;
  --success-bg: rgba(52, 211, 153, 0.12);
  --warning: #fbbf24;
  --warning-bg: rgba(251, 191, 36, 0.12);
  --error: #f87171;
  --error-bg: rgba(248, 113, 113, 0.12);
  --info: #60a5fa;
  --progress-bg: rgba(255, 255, 255, 0.06);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
  --font: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
  --font-mono: "Cascadia Code", "JetBrains Mono", "SF Mono", Consolas, monospace;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
}

.light {
  --bg-app: #e8ecf0;
  --bg-surface: rgba(255, 255, 255, 0.55);
  --bg-card: rgba(255, 255, 255, 0.6);
  --bg-input: transparent;
  --bg-hover: rgba(0, 0, 0, 0.04);
  --border: rgba(0, 0, 0, 0.06);
  --border-hover: rgba(0, 0, 0, 0.12);
  --border-active: rgba(91, 154, 255, 0.5);
  --text-primary: #1a1a2e;
  --text-secondary: #3f4759;
  --text-muted: #6b758b;
  --text-dim: rgba(107, 117, 139, 0.45);
  --progress-bg: rgba(0, 0, 0, 0.04);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.12);
}

html, body {
  height: 100%;
  background: var(--bg-app);
  color: var(--text-primary);
  font-family: var(--font);
  font-size: 14px;
  font-weight: var(--font-weight-normal);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

#app {
  height: 100%;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.08); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.16); }

.light ::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); }
.light ::-webkit-scrollbar-thumb:hover { background: rgba(0,0,0,0.18); }
</style>

<style scoped>
.app {
  height: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 28px;
  position: relative;
  overflow: hidden;
}

.app-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.bg-video {
  position: fixed;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  pointer-events: none;
  filter: brightness(0.85);
}

.bg-vignette {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  background: radial-gradient(ellipse at center, transparent 35%, rgba(8,8,12,0.75) 100%);
}

.light .bg-vignette {
  background: radial-gradient(ellipse at center, transparent 50%, rgba(200,210,220,0.3) 100%);
}

/* ── Landing ── */
.landing {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
}

.landing-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.landing-logo {
  width: 80px;
  height: 80px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 0 40px rgba(91, 154, 255, 0.3);
}

.landing-logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  animation: logo-init 0.8s ease-out forwards;
}

@keyframes logo-init {
  from { transform: rotate(-5deg) scale(0.92); opacity: 0; }
  to { transform: rotate(0deg) scale(1); opacity: 1; }
}

.landing-title {
  font-size: 40px;
  font-weight: 300;
  color: #fff;
  letter-spacing: 6px;
  text-shadow: 0 2px 30px rgba(0,0,0,0.4);
}

.light .landing-title {
  color: var(--text-primary);
  text-shadow: none;
}

.landing-desc {
  font-size: 13px;
  color: rgba(255,255,255,0.4);
  letter-spacing: 3px;
  font-weight: 300;
}

.light .landing-desc {
  color: var(--text-muted);
}

.light .dir-path {
  color: var(--text-secondary);
  background: rgba(0, 0, 0, 0.06);
}

.landing-btn {
  margin-top: 16px;
  padding: 12px 40px;
  border: 1px solid rgba(255,255,255,0.25);
  border-radius: 100px;
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: rgba(255,255,255,0.9);
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 1px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s;
}

.landing-btn:hover {
  background: rgba(255,255,255,0.14);
  border-color: rgba(255,255,255,0.5);
  transform: translateY(-1px);
  box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}

.light .landing-btn {
  border-color: rgba(0,0,0,0.15);
  background: rgba(255,255,255,0.4);
  color: var(--text-primary);
}

.light .landing-btn:hover {
  background: rgba(255,255,255,0.65);
  border-color: rgba(0,0,0,0.3);
}

/* ── Header ── */
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(91, 154, 255, 0.3);
}

.logo-img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.app-title {
  font-size: 17px;
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.app-badge {
  font-size: 10px;
  font-weight: var(--font-weight-semibold);
  color: var(--accent);
  background: var(--accent-glow);
  padding: 1px 7px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-theme {
  width: 34px;
  height: 34px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.btn-theme:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-glow);
}

.dir-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.dir-path {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-hover);
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  max-width: 280px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: var(--font-mono);
}

.btn-ghost {
  padding: 4px 12px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-ghost:hover {
  border-color: var(--accent);
  color: var(--accent);
  background: var(--accent-glow);
}

.app-main {
  flex: 1;
  display: flex;
  gap: 20px;
  padding-bottom: 28px;
  min-height: 0;
  position: relative;
  z-index: 2;
}

.panel {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  overflow: auto;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: var(--shadow-sm);
}

.panel-left {
  flex: 1;
  min-width: 0;
}

.panel-right {
  width: 420px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

@media (max-width: 860px) {
  .app-main { flex-direction: column; }
  .panel-right { width: auto; max-height: 380px; }
}

/* ── Completed notification ── */
.completed-notif {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  backdrop-filter: blur(12px);
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  min-width: 240px;
}

.notif-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--success-bg);
  color: var(--success);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 13px;
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

.notif-file {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── Transitions ── */
.notif-enter-active { transition: all 0.3s ease-out; }
.notif-leave-active { transition: all 0.2s ease-in; }
.notif-enter-from { opacity: 0; transform: translateX(-50%) translateY(-12px); }
.notif-leave-to { opacity: 0; transform: translateX(-50%) translateY(-8px); }
.landing-leave-enter-active { transition: all 0.5s ease-out; }
.landing-leave-leave-active { transition: all 0.35s ease-in; }
.landing-leave-enter-from { opacity: 0; transform: translateY(-20px); }
.landing-leave-leave-to { opacity: 0; transform: translateY(-20px); }

.app-enter-enter-active { transition: all 0.5s ease-out 0.15s; }
.app-enter-leave-active { transition: all 0.2s ease-in; }
.app-enter-enter-from { opacity: 0; transform: translateY(24px); }
.app-enter-leave-to { opacity: 0; transform: translateY(-5px); }
</style>
