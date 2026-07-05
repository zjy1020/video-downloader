# 视频/图文解析下载工具 V1 — 设计文档

日期: 2026-07-05
项目: video-downloader

## 概述

一个本地运行的 Web 工具，输入抖音或 B 站分享链接，解析出资源直链并下载到本地磁盘。

## 技术栈

- 前端: Vue3 + Vite + Axios
- 后端: Python FastAPI + requests

## 项目结构

```
video-downloader/
├── backend/
│   ├── main.py          # FastAPI 入口，路由 + CORS + 启动
│   ├── parser.py        # 调用 bugpk.com API，标准化返回
│   ├── downloader.py    # requests 下载文件到本地
│   └── config.py        # 下载目录管理（读写 JSON 配置文件）
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       └── App.vue      # 单页面组件
└── docs/superpowers/specs/
    └── 2026-07-05-video-downloader-design.md
```

## 后端设计

### 模块职责

#### config.py
- 维护一个本地 JSON 文件 `download_config.json`，存 `download_dir` 字段
- 提供 `get_download_dir()` 和 `set_download_dir(path)` 两个函数
- 默认目录为 `./downloads`（相对于 `backend/` 目录）

#### parser.py
- `parse_url(url: str) → dict`
- 根据 URL 域名判断平台（douyin.com / b23.tv）
- 调用对应第三方 API（`api.bugpk.com/api/douyin` 或 `api.bugpk.com/api/bilibili`）
- 标准化返回:
  ```json
  {
    "title": "视频标题",
    "platform": "douyin",
    "type": "video | image | live",
    "files": [
      {"index": 1, "title": "文件1", "url": "直链", "type": "video"},
      {"index": 2, "title": "文件2", "url": "直链", "type": "image"}
    ]
  }
  ```
- 单视频: files 长度为 1
- B 集合: 判断 `data.totalVideos > 1` 则遍历 `data.videos`，排除 `duration < 5` 的无效片段
- B 单视频: 即使 `totalVideos == 1` 也取 `data.videos[0]`，因为 `data.url` 可能不准确
- 抖音图文: files 包含所有图片 URL，type 为 `image`
- 抖音实况: files 中每条为 `{"type": "live_photo", "index": n, "title": "实况_{n}", "image": "静态图URL", "video": "动态视频URL"}`，下载时只下载 video（动态视频）
- 抖音视频: 优先取 `data.url`，若为空则取 `data.video_backup[0]`
- 格式兼容: 对 B 站返回中的 `\u002F` 或转义斜杠做简单清理

#### downloader.py
- `download_file(url: str, filename: str, target_dir: str) → dict`
- 用 requests stream 模式下载
- 文件名: 取 API 返回的标题，过滤掉 `\/:*?"<>|` 等非法字符，截断 100 字，否则用随机 UUID
- 自动补扩展名（.mp4 / .jpg / .png 等，根据 Content-Type 或 URL 后缀）
- 合集文件: 文件名加序号前缀，如 `01_标题.mp4`
- 返回 `{"status": "ok", "path": "完整路径"}` 或 `{"status": "error", "message": "..."}`

#### main.py
- FastAPI 应用，注册 CORS（允许前端 localhost 跨域）
- 三个路由:

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/parse` | 接收 `{"url": "..."}`, 返回解析结果 |
| POST | `/download` | 接收 `{"url": "...", "filename": "..."}`, 下载文件 |
| GET | `/download_dir` | 返回当前下载目录 `{"path": "..."}` |
| POST | `/set_download_dir` | 接收 `{"path": "..."}`, 设置下载目录 |

## 前端设计

### 单页布局（App.vue）

```
┌──────────────────────────────────────────┐
│  视频/图文解析下载工具                      │
├──────────────────────────────────────────┤
│  下载目录: /path/to/downloads   [更改]    │
├──────────────────────────────────────────┤
│  ┌──────────────────────────────────┐    │
│  │ 粘贴抖音或B站链接...             │    │
│  └──────────────────────────────────┘    │
│           [ 解析 ]                       │
├──────────────────────────────────────────┤
│  解析结果:                              │
│  [x] 视频标题1                    [下载] │
│  [x] 视频标题2                    [下载] │
│                     [下载全部]           │
└──────────────────────────────────────────┘
```

### 交互流程

1. 页面加载 → `GET /download_dir` 获取当前下载目录，展示在顶部
2. 点 [更改] → `prompt()` 输路径 → `POST /set_download_dir`
3. 粘链接 → 点 [解析] → `POST /parse` → 展示结果列表（标题 + 类型）
4. 点单条 [下载] → 按钮变"下载中..."（disabled）→ `POST /download` → 完成后变"已完成" 或弹错误
5. 点 [下载全部] → 逐个调用 `/download`，每条独立更新状态

### 状态管理

- 使用 Vue3 `ref` / `reactive`，不引入 Vuex/Pinia
- 关键状态: `downloadDir`, `parsedItems[]`, `downloadStatus{}`

## 错误处理

- 网络错误: 前端 catch 后 `alert()` 提示
- 解析失败（无效链接/平台不支持）: 后端返回 `{"code": 400, "msg": "..."}`
- 下载失败（链接过期/磁盘满）: 后端返回 error status，前端标记该条为"下载失败"

## 限制（V1 不做）

- 不做 UI 美化
- 不做登录
- 不做数据库
- 不做批量队列持久化
- 不做大文件分片下载
- 不做多平台扩展
