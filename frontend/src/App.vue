<template>
  <div class="app">
    <div class="bg-glow glow-1"></div>
    <div class="bg-glow glow-2"></div>

    <header class="app-header">
      <div class="header-left">
        <div class="logo">
          <img src="/logo.png" alt="logo" class="logo-img" />
        </div>
        <h1 class="app-title">解析</h1>
        <span class="app-badge">V2</span>
      </div>
      <div class="header-right">
        <span class="dir-label">下载目录</span>
        <code class="dir-path" :title="downloadDir">{{ downloadDir }}</code>
        <button class="btn-ghost" @click="changeDir">更改</button>
      </div>



    </header>

    <main class="app-main">
      <section class="panel panel-left">
        <InputPanel @tasks-added="onTasksAdded" />
      </section>
      <section class="panel panel-right">
        <TaskList
          :tasks="tasks"
          @retry="refreshTasks"
          @delete="refreshTasks"
        />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import InputPanel from './components/InputPanel.vue'
import TaskList from './components/TaskList.vue'

const API_BASE = '/api'
const downloadDir = ref('')
const tasks = ref([])
let pollTimer = null

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
  try {
    const dirHandle = await window.showDirectoryPicker({ mode: 'read' })
    let found = false
    for await (const entry of dirHandle.values()) {
      if (entry.kind === 'file') {
        const file = await entry.getFile()
        if (file.path) {
          setDir(file.path.slice(0, -(entry.name.length)))
          found = true
          break
        }
      }
    }
    if (!found) {
      const path = prompt('无法获取完整路径，请手动输入下载目录：', downloadDir.value)
      if (path) setDir(path.trim())
    }
  } catch {
    const path = prompt('输入下载目录路径：', downloadDir.value)
    if (path) setDir(path.trim())
  }
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

async function fetchTasks() {
  try {
    const res = await axios.get(`${API_BASE}/tasks`)
    tasks.value = res.data.data
    saveTasksToCache(res.data.data)
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
  --bg-app: #0a0a0f;
  --bg-surface: rgba(255, 255, 255, 0.03);
  --bg-card: rgba(255, 255, 255, 0.04);
  --bg-input: rgba(255, 255, 255, 0.05);
  --bg-hover: rgba(255, 255, 255, 0.06);
  --border: rgba(255, 255, 255, 0.08);
  --border-hover: rgba(255, 255, 255, 0.15);
  --border-active: rgba(91, 154, 255, 0.5);
  --accent: #5b9aff;
  --accent-hover: #7bb0ff;
  --accent-glow: rgba(91, 154, 255, 0.2);
  --text-primary: #e8ecf4;
  --text-secondary: #8b95a8;
  --text-muted: #5a6377;
  --success: #34d399;
  --success-bg: rgba(52, 211, 153, 0.12);
  --warning: #fbbf24;
  --warning-bg: rgba(251, 191, 36, 0.12);
  --error: #f87171;
  --error-bg: rgba(248, 113, 113, 0.12);
  --info: #60a5fa;
  --progress-bg: rgba(255, 255, 255, 0.08);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);
  --font: -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", "Helvetica Neue", sans-serif;
  --font-mono: "Cascadia Code", "JetBrains Mono", "SF Mono", Consolas, monospace;
}

html, body {
  height: 100%;
  background: var(--bg-app);
  color: var(--text-primary);
  font-family: var(--font);
  font-size: 14px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

#app {
  height: 100%;
}

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
</style>

<style scoped>
.app {
  height: 100%;
  display: flex;
  flex-direction: column;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 28px;
  position: relative;
  overflow: hidden;
}

.bg-glow {
  position: fixed;
  width: 600px;
  height: 600px;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(120px);
  opacity: 0.08;
  z-index: 0;
}

.glow-1 {
  background: var(--accent);
  top: -200px;
  left: -200px;
}

.glow-2 {
  background: #a78bfa;
  bottom: -300px;
  right: -200px;
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 0;
  flex-shrink: 0;
  position: relative;
  z-index: 1;
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
  font-weight: 600;
  color: var(--text-primary);
  letter-spacing: -0.3px;
}

.app-badge {
  font-size: 10px;
  font-weight: 600;
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

.dir-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.dir-path {
  font-size: 11px;
  color: var(--text-muted);
  background: var(--bg-input);
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
  padding: 16px 0 24px;
  overflow: hidden;
  position: relative;
  z-index: 1;
}

.panel {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 20px;
  overflow: auto;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: var(--shadow-md);
}

.panel-left {
  flex: 1;
  min-width: 0;
}

.panel-right {
  width: 420px;
  flex-shrink: 0;
}

@media (max-width: 860px) {
  .app-main { flex-direction: column; }
  .panel-right { width: auto; max-height: 380px; }
}
</style>
