# 视频/图文解析下载工具

B站 / 抖音视频 & 图文链接解析下载工具，Tauri v2 桌面版。

## 快速开始

> **需要：** Python 3.8+、Node.js 18+、Git
>
> 没装 Python？→ https://www.python.org/downloads/（装的时候勾选"Add Python to PATH"）

```bash
# 1. 克隆
git clone https://github.com/zjy1020/video-downloader
cd video-downloader

# 2. 安装 Python 依赖（一条命令，pip 自带无需额外安装）
pip install -r backend/requirements.txt

# 3. 安装前端依赖
cd frontend && npm install && cd ..

# 4. 启动！（双击 start.bat 也行）
start.bat
```

浏览器打开 **http://127.0.0.1:3000**

## 功能

- 解析 B站 / 抖音分享链接（视频、图文）
- 多线程并行下载、自动 dedup 命名
- B站画质选择（360P ~ 4K/HDR）
- 剪贴板监听：复制链接自动提示解析
- 下载速度 / 剩余时间显示
- 深色/浅色主题切换

## 切换解析接口

解析接口在 `backend/parser.py` 顶部配置：

```python
BILIBILI_API = "https://api.bugpk.com/api/bilibili"
DOUYIN_API = "https://api.bugpk.com/api/douyin"
```

默认使用 `bugpk.com` 聚合接口。失效时可替换为其他同类服务，或启用 B站原生 API（已内置 `api.bilibili.com` 作为备用）。

B站解析走两条路径：
1. `bugpk.com` 聚合接口（优先）
2. `api.bilibili.com` 原生 API（备用）

抖音接口失效时自动走 mock 数据保底。

## 目录结构

```
video-downloader/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── parser.py            # 链接解析（B站/抖音）
│   ├── downloader.py        # 多线程下载引擎
│   ├── task_manager.py      # 任务队列管理
│   ├── naming.py            # 文件命名 / 去重
│   ├── config.py            # 下载目录配置
│   ├── requirements.txt     # Python 依赖清单
│   ├── build-backend.bat    # PyInstaller 打包脚本
│   └── download_config.json # 持久化配置
├── frontend/
│   ├── src/
│   │   ├── App.vue          # 主界面（含 loading 屏）
│   │   ├── components/      # UI 组件
│   │   ├── composables/     # Vue composables
│   │   └── lib/api.js       # API 地址（自动区分 Tauri/浏览器）
│   ├── src-tauri/           # Tauri v2 桌面壳
│   │   ├── src/lib.rs       # Rust 入口（含 sidecar 启动）
│   │   ├── binaries/        # PyInstaller 输出目录
│   │   └── tauri.conf.json  # Tauri 配置
│   └── package.json
├── downloads/               # 默认下载目录
├── start.bat                # 一键启动（含自动装依赖）
└── stop.bat                 # 停止开发环境
```

## 构建打包

### 1. 打包 Python 后端为 exe

```bash
cd backend
.\build-backend.bat
```

输出：`frontend/src-tauri/binaries/python-backend-x86_64-pc-windows-msvc.exe`

### 2. 构建 Tauri 安装包（包含前后端）

```bash
cd frontend
npx tauri build
```

输出：`frontend/src-tauri/target/release/bundle/nsis/视频解析下载_0.1.0_x64-setup.exe`

安装包包含所有依赖，用户无需安装 Python 或 Node.js。

## License

MIT License

Copyright (c) 2026 ZJY1020