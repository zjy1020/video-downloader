<template>
  <div style="max-width: 800px; margin: 40px auto; padding: 0 20px; font-family: system-ui, sans-serif;">
    <h2>视频/图文解析下载工具</h2>

    <div style="margin: 12px 0; padding: 8px 12px; background: #f5f5f5; border-radius: 4px; display: flex; align-items: center; gap: 8px;">
      <span style="font-size: 13px; color: #666;">下载目录:</span>
      <code style="font-size: 13px; flex: 1;">{{ downloadDir }}</code>
      <button @click="changeDir" style="padding: 2px 10px; cursor: pointer;">更改</button>
    </div>

    <div style="display: flex; gap: 8px; margin: 16px 0;">
      <input
        v-model="urlInput"
        placeholder="粘贴抖音或B站分享链接..."
        style="flex: 1; padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;"
        @keyup.enter="parse"
      />
      <button @click="parse" :disabled="parsing" style="padding: 8px 20px; cursor: pointer;">
        {{ parsing ? '解析中...' : '解析' }}
      </button>
    </div>

    <div v-if="parseResult" style="margin-top: 16px;">

      <img
        v-if="parseResult.cover"
        :src="proxyUrl(parseResult.cover)"
        @click="previewImg = parseResult.cover"
        style="width: 100%; max-height: 300px; object-fit: cover; border-radius: 6px; margin-bottom: 12px; cursor: pointer; border: 1px solid #ddd;"
      />

      <h4 style="margin: 0 0 12px;">{{ parseResult.title }}</h4>

      <div v-if="parseResult.type === 'image'" style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 16px;">
        <div v-for="file in parseResult.files" :key="file.index"
          :style="{
            width: 'calc(25% - 10px)',
            minWidth: '150px',
            border: '2px solid ' + (selected[file.index] ? '#4caf50' : '#ddd'),
            borderRadius: '6px',
            overflow: 'hidden',
            cursor: 'pointer',
            position: 'relative',
            background: '#fafafa'
          }"
          @click="toggleSelect(file.index)">
          <img :src="file.url" style="width: 100%; height: 150px; object-fit: cover; display: block;" />
          <div style="position: absolute; top: 6px; left: 6px; width: 20px; height: 20px; border-radius: 3px; background: rgba(255,255,255,0.9); display: flex; align-items: center; justify-content: center; font-size: 13px; border: 1px solid #999;">
            <span v-if="selected[file.index]" style="color: #4caf50;">✓</span>
          </div>
          <div style="padding: 4px 6px; font-size: 11px; color: #666;">
            {{ file.title }}
            <span v-if="file.size"> ({{ formatSize(file.size) }})</span>
          </div>
        </div>
        <div style="width: 100%; margin-top: 8px;">
          <button
            @click="downloadSelected"
            :disabled="downloadingAll || selectedCount === 0"
            style="padding: 8px 24px; cursor: pointer;">
            下载选中图片 ({{ selectedCount }})
          </button>
        </div>
      </div>

      <div v-else>
        <div v-for="file in parseResult.files" :key="file.index"
          style="display: flex; align-items: center; gap: 8px; padding: 10px 12px; margin: 6px 0; background: #fafafa; border-radius: 4px; border: 1px solid #eee;">
          <input type="checkbox" v-model="selected[file.index]" style="cursor: pointer;" />

          <span v-if="parseResult.cover && file.type === 'video'" style="flex: 1; display: flex; align-items: center; gap: 8px;">
            <img :src="proxyUrl(parseResult.cover)" style="width: 120px; height: 68px; object-fit: cover; border-radius: 4px;" />
            <span>
              <div style="font-size: 14px;">▶ {{ file.title }}</div>
              <div v-if="file.size" style="font-size: 12px; color: #888;">{{ formatSize(file.size) }}</div>
            </span>
          </span>
          <span v-else style="font-size: 14px; flex: 1;">📄 {{ file.title }}</span>

          <div v-if="fileProgress[file.index]" style="display: flex; align-items: center; gap: 6px; min-width: 140px;">
            <div style="width: 80px; height: 6px; background: #e0e0e0; border-radius: 3px;">
              <div :style="{ width: (fileProgress[file.index].progress * 100) + '%', height: '6px', background: '#4caf50', borderRadius: '3px', transition: 'width 0.3s' }"></div>
            </div>
            <span style="font-size: 12px; color: #666;">{{ Math.round(fileProgress[file.index].progress * 100) }}%</span>
          </div>
          <span v-else-if="fileDone[file.index]" style="font-size: 12px; color: #4caf50;">已完成</span>

          <button
            @click="download(file)"
            :disabled="fileProgress[file.index] || fileDone[file.index]"
            style="padding: 4px 14px; cursor: pointer; font-size: 13px;">
            {{ fileDone[file.index] ? '已完成' : fileProgress[file.index] ? '下载中' : '下载' }}
          </button>
        </div>

        <div v-if="parseResult.files.length > 0" style="display: flex; gap: 8px; margin-top: 10px;">
          <button
            @click="downloadSelected"
            :disabled="downloadingAll || selectedCount === 0"
            style="padding: 6px 20px; cursor: pointer;">
            下载选中 ({{ selectedCount }})
          </button>
          <button
            v-if="parseResult.files.length > 1"
            @click="downloadAll"
            :disabled="downloadingAll"
            style="padding: 6px 20px; cursor: pointer;">
            {{ downloadingAll ? '下载中...' : '下载全部' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="previewImg" style="position: fixed; inset: 0; background: rgba(0,0,0,0.85); display: flex; align-items: center; justify-content: center; z-index: 999;" @click="previewImg = ''">
      <img :src="previewImg" style="max-width: 90%; max-height: 90%; border-radius: 8px;" />
    </div>

    <div v-if="error" style="margin-top: 12px; padding: 8px 12px; background: #fff0f0; color: #c00; border-radius: 4px; font-size: 14px;">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

const urlInput = ref('')
const downloadDir = ref('')
const parseResult = ref(null)
const parsing = ref(false)
const downloadingAll = ref(false)
const error = ref('')
const previewImg = ref('')
const selected = ref({})
const fileProgress = ref({})
const fileDone = ref({})

const selectedCount = computed(() => Object.values(selected.value).filter(Boolean).length)

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

function toggleSelect(index) {
  selected.value[index] = !selected.value[index]
}

async function getDownloadDir() {
  const res = await axios.get(`${API_BASE}/download_dir`)
  downloadDir.value = res.data.path
}

async function changeDir() {
  const path = prompt('输入下载目录路径：', downloadDir.value)
  if (path) {
    await axios.post(`${API_BASE}/set_download_dir`, { path })
    downloadDir.value = path
  }
}

async function parse() {
  if (!urlInput.value.trim()) return
  error.value = ''
  parseResult.value = null
  previewImg.value = ''
  selected.value = {}
  fileProgress.value = {}
  fileDone.value = {}
  parsing.value = true
  try {
    const res = await axios.post(`${API_BASE}/parse`, { url: urlInput.value })
    if (res.data.code === 200) {
      parseResult.value = res.data.data
      for (const f of res.data.data.files) {
        selected.value[f.index] = true
      }
    } else {
      error.value = res.data.msg
    }
  } catch (e) {
    error.value = '解析请求失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    parsing.value = false
  }
}

async function pollProgress(taskId, fileIndex) {
  const poll = async () => {
    try {
      const res = await axios.get(`${API_BASE}/download/progress/${taskId}`)
      const d = res.data.data
      fileProgress.value[fileIndex] = d
      if (d.status === 'done') {
        delete fileProgress.value[fileIndex]
        fileDone.value[fileIndex] = true
        return
      }
      if (d.status === 'error') {
        delete fileProgress.value[fileIndex]
        error.value = d.message
        return
      }
      setTimeout(poll, 500)
    } catch {
      setTimeout(poll, 500)
    }
  }
  poll()
}

async function download(file) {
  try {
    const res = await axios.post(`${API_BASE}/download`, { url: file.url, filename: file.title })
    if (res.data.code === 200) {
      const taskId = res.data.data.task_id
      pollProgress(taskId, file.index)
    } else {
      error.value = res.data.msg
    }
  } catch (e) {
    error.value = '下载请求失败: ' + (e.response?.data?.detail || e.message)
  }
}

async function downloadSelected() {
  if (!parseResult.value) return
  downloadingAll.value = true
  for (const file of parseResult.value.files) {
    if (selected.value[file.index] && !fileDone.value[file.index]) {
      await download(file)
    }
  }
  downloadingAll.value = false
}

async function downloadAll() {
  if (!parseResult.value) return
  downloadingAll.value = true
  for (const file of parseResult.value.files) {
    if (!fileDone.value[file.index]) {
      await download(file)
    }
  }
  downloadingAll.value = false
}

onMounted(getDownloadDir)
</script>
