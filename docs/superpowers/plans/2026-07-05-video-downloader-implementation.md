# 视频/图文解析下载工具 V1 Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 一个可运行的本地工具，输入抖音/B站链接 → 解析资源信息 → 下载到本地指定目录

**Architecture:** FastAPI 后端提供三个核心接口（解析/下载/目录配置），Vue3 前端单页应用通过 Axios 调用。解析层优先调第三方 API，失败时 fallback 到 mock 数据保证流程可演示。

**Tech Stack:** Python FastAPI + requests, Vue3 + Vite + Axios

---

## File Structure

```
video-downloader/
├── backend/
│   ├── config.py          # 下载目录配置管理（JSON 文件）
│   ├── parser.py          # URL 解析 + 第三方 API 调用 + mock fallback
│   ├── downloader.py      # requests 流式下载 + 文件名处理
│   └── main.py            # FastAPI 入口 + 路由 + CORS
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.js        # Vue 应用入口
│       └── App.vue        # 单页面组件
```

---

### Task 1: 后端目录配置模块 (config.py)

**Files:**
- Create: `backend/config.py`

- [ ] **Step 1: 创建 config.py**

```python
import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "download_config.json")
DEFAULT_DIR = os.path.join(os.path.dirname(__file__), "downloads")


def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_download_dir():
    cfg = _load_config()
    return cfg.get("download_dir", DEFAULT_DIR)


def set_download_dir(path):
    _save_config({"download_dir": path})
```

---

### Task 2: 后端解析模块 (parser.py)

**Files:**
- Create: `backend/parser.py`

- [ ] **Step 1: 创建 parser.py**

```python
import re
import requests
import uuid

BILIBILI_API = "https://api.bugpk.com/api/bilibili"
DOUYIN_API = "https://api.bugpk.com/api/douyin"


def _clean_title(title):
    if not title:
        return str(uuid.uuid4())[:8]
    cleaned = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    return cleaned[:100] or str(uuid.uuid4())[:8]


def _detect_platform(url):
    if "douyin.com" in url or "iesdouyin.com" in url:
        return "douyin"
    if "b23.tv" in url or "bilibili.com" in url:
        return "bilibili"
    return None


def _mock_bilibili(url):
    return {
        "title": "测试B站视频标题",
        "platform": "bilibili",
        "type": "video",
        "files": [
            {"index": 1, "title": "测试视频1", "url": "", "type": "video"},
            {"index": 2, "title": "测试视频2", "url": "", "type": "video"},
        ]
    }


def _mock_douyin(url):
    return {
        "title": "测试抖音视频标题",
        "platform": "douyin",
        "type": "video",
        "files": [
            {"index": 1, "title": "测试视频1", "url": "", "type": "video"},
        ]
    }


def _parse_bilibili(url):
    try:
        resp = requests.get(BILIBILI_API, params={"url": url}, timeout=15)
        data = resp.json()
        if data.get("code") != 200:
            return _mock_bilibili(url)

        raw = data["data"]
        videos = raw.get("videos", [])
        total = raw.get("totalVideos", len(videos))

        files = []
        for v in videos:
            files.append({
                "index": v.get("index", len(files) + 1),
                "title": _clean_title(v.get("title", "无标题")),
                "url": v.get("url", ""),
                "type": "video",
            })

        return {
            "title": _clean_title(raw.get("title", "")),
            "platform": "bilibili",
            "type": "video",
            "files": files,
        }
    except Exception:
        return _mock_bilibili(url)


def _parse_douyin(url):
    try:
        resp = requests.get(DOUYIN_API, params={"url": url}, timeout=15)
        data = resp.json()
        if data.get("code") != 200:
            return _mock_douyin(url)

        raw = data["data"]
        content_type = raw.get("type", "video")
        files = []

        if content_type == "video":
            video_url = raw.get("url") or (raw.get("video_backup") or [None])[0]
            if video_url:
                files.append({
                    "index": 1,
                    "title": _clean_title(raw.get("title", "视频")),
                    "url": video_url,
                    "type": "video",
                })
        elif content_type == "image":
            for i, img_url in enumerate(raw.get("images", [])):
                files.append({
                    "index": i + 1,
                    "title": f"图片_{i + 1}",
                    "url": img_url,
                    "type": "image",
                })
        elif content_type == "live":
            for i, item in enumerate(raw.get("live_photo", [])):
                video_url = item.get("video", "")
                if video_url:
                    files.append({
                        "index": i + 1,
                        "title": f"实况_{i + 1}",
                        "url": video_url,
                        "type": "video",
                    })

        return {
            "title": _clean_title(raw.get("title", "")),
            "platform": "douyin",
            "type": content_type,
            "files": files,
        }
    except Exception:
        return _mock_douyin(url)


def parse_url(url):
    platform = _detect_platform(url)
    if platform == "bilibili":
        return _parse_bilibili(url)
    elif platform == "douyin":
        return _parse_douyin(url)
    else:
        return {"title": "不支持的链接", "platform": "unknown", "type": "unknown", "files": []}
```

---

### Task 3: 后端下载模块 (downloader.py)

**Files:**
- Create: `backend/downloader.py`

- [ ] **Step 1: 创建 downloader.py**

```python
import os
import requests
from urllib.parse import unquote, urlparse


def _get_extension(url, content_type):
    if content_type:
        mapping = {
            "video/mp4": ".mp4",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }
        for mime, ext in mapping.items():
            if mime in content_type:
                return ext
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    if ext and len(ext) <= 5:
        return ext
    return ".mp4"


def download_file(url, filename, target_dir):
    if not url:
        return {"status": "error", "message": "下载链接为空"}

    os.makedirs(target_dir, exist_ok=True)

    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            ext = _get_extension(url, r.headers.get("Content-Type", ""))
            save_name = f"{filename}{ext}"
            save_path = os.path.join(target_dir, save_name)

            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            return {"status": "ok", "path": save_path}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

---

### Task 4: 后端入口 (main.py)

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from parser import parse_url
from downloader import download_file
from config import get_download_dir, set_download_dir

app = FastAPI(title="视频解析下载工具")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    filename: str


class SetDirRequest(BaseModel):
    path: str


@app.post("/parse")
def parse(req: ParseRequest):
    result = parse_url(req.url)
    if not result["files"]:
        return {"code": 400, "msg": "解析失败，未找到可下载的资源", "data": result}
    return {"code": 200, "msg": "解析成功", "data": result}


@app.post("/download")
def download(req: DownloadRequest):
    target_dir = get_download_dir()
    result = download_file(req.url, req.filename, target_dir)
    if result["status"] == "ok":
        return {"code": 200, "msg": "下载成功", "data": result}
    return {"code": 500, "msg": result["message"], "data": None}


@app.get("/download_dir")
def get_dir():
    return {"code": 200, "path": get_download_dir()}


@app.post("/set_download_dir")
def set_dir(req: SetDirRequest):
    set_download_dir(req.path)
    return {"code": 200, "path": get_download_dir()}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

### Task 5: 前端项目脚手架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/index.html`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "video-downloader-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "axios": "^1.7.0"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "vite": "^5.0.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.js**

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})
```

- [ ] **Step 3: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>视频/图文解析下载工具</title>
</head>
<body>
  <div id="app"></div>
  <script type="module" src="/src/main.js"></script>
</body>
</html>
```

---

### Task 6: 前端入口文件 (main.js)

**Files:**
- Create: `frontend/src/main.js`

- [ ] **Step 1: 创建 main.js**

```js
import { createApp } from 'vue'
import App from './App.vue'

createApp(App).mount('#app')
```

---

### Task 7: 前端主页面 (App.vue)

**Files:**
- Create: `frontend/src/App.vue`

- [ ] **Step 1: 创建 App.vue**

```vue
<template>
  <div style="max-width: 700px; margin: 40px auto; padding: 0 20px; font-family: system-ui, sans-serif;">
    <h2>视频/图文解析下载工具</h2>

    <div style="margin: 12px 0; padding: 8px 12px; background: #f5f5f5; border-radius: 4px; display: flex; align-items: center; gap: 8px;">
      <span style="font-size: 13px; color: #666;">下载目录:</span>
      <code style="font-size: 13px; flex: 1;">{{ downloadDir }}</code>
      <button @click="changeDir" style="padding: 2px 10px; cursor: pointer;">更改</button>
    </div>

    <div style="display: flex; gap: 8px; margin: 16px 0;">
      <input
        v-model="urlInput"
        placeholder="粘贴抖音或B站链接..."
        style="flex: 1; padding: 8px 12px; border: 1px solid #ccc; border-radius: 4px; font-size: 14px;"
        @keyup.enter="parse"
      />
      <button @click="parse" :disabled="parsing" style="padding: 8px 20px; cursor: pointer;">
        {{ parsing ? '解析中...' : '解析' }}
      </button>
    </div>

    <div v-if="parseResult" style="margin-top: 16px;">
      <h4 style="margin: 0 0 8px;">解析结果: {{ parseResult.title }}</h4>
      <div v-for="file in parseResult.files" :key="file.index"
        style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; margin: 4px 0; background: #fafafa; border-radius: 4px; border: 1px solid #eee;">
        <span style="font-size: 14px;">{{ file.title }}</span>
        <button
          @click="download(file)"
          :disabled="downloadStatus[file.index] === 'downloading'"
          style="padding: 4px 14px; cursor: pointer; font-size: 13px;">
          {{ downloadStatus[file.index] || '下载' }}
        </button>
      </div>
      <button
        v-if="parseResult.files.length > 1"
        @click="downloadAll"
        :disabled="downloadingAll"
        style="margin-top: 8px; padding: 6px 20px; cursor: pointer;">
        {{ downloadingAll ? '下载中...' : '下载全部' }}
      </button>
    </div>

    <div v-if="error" style="margin-top: 12px; padding: 8px 12px; background: #fff0f0; color: #c00; border-radius: 4px; font-size: 14px;">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const API_BASE = '/api'

const urlInput = ref('')
const downloadDir = ref('')
const parseResult = ref(null)
const parsing = ref(false)
const downloadingAll = ref(false)
const downloadStatus = ref({})
const error = ref('')

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
  parsing.value = true
  downloadStatus.value = {}
  try {
    const res = await axios.post(`${API_BASE}/parse`, { url: urlInput.value })
    if (res.data.code === 200) {
      parseResult.value = res.data.data
    } else {
      error.value = res.data.msg
    }
  } catch (e) {
    error.value = '解析请求失败: ' + (e.response?.data?.detail || e.message)
  } finally {
    parsing.value = false
  }
}

async function download(file) {
  downloadStatus.value[file.index] = '下载中...'
  try {
    const res = await axios.post(`${API_BASE}/download`, {
      url: file.url,
      filename: file.title
    })
    if (res.data.code === 200) {
      downloadStatus.value[file.index] = '已完成'
    } else {
      downloadStatus.value[file.index] = '下载失败'
      error.value = res.data.msg
    }
  } catch (e) {
    downloadStatus.value[file.index] = '下载失败'
    error.value = '下载请求失败: ' + (e.response?.data?.detail || e.message)
  }
}

async function downloadAll() {
  if (!parseResult.value) return
  downloadingAll.value = true
  for (const file of parseResult.value.files) {
    if (downloadStatus.value[file.index] === '已完成') continue
    await download(file)
  }
  downloadingAll.value = false
}

onMounted(getDownloadDir)
</script>
```

---

### Task 8: 安装依赖 & 启动验证

**Files:** (no file changes)

- [ ] **Step 1: 安装后端依赖**

```bash
cd Desktop/video-downloader/backend
pip install fastapi uvicorn requests
```

- [ ] **Step 2: 安装前端依赖**

```bash
cd Desktop/video-downloader/frontend
npm install
```

- [ ] **Step 3: 启动后端（开一个终端）**

```bash
cd Desktop/video-downloader/backend
python main.py
```
预期: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 4: 启动前端（开另一个终端）**

```bash
cd Desktop/video-downloader/frontend
npm run dev
```
预期: `Vite dev server running at http://localhost:3000`

- [ ] **Step 5: 完整流程验证**

1. 浏览器打开 `http://localhost:3000`
2. 看到顶部下载目录路径，点击「更改」可以修改
3. 输入一个链接（如 `https://b23.tv/XhtfoyZ`），点击「解析」
4. 看到标题和文件列表
5. 点击「下载」，按钮变「下载中...」→「已完成」
6. 检查下载目录，确认文件已保存
