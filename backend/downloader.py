import os
import requests
import threading
from urllib.parse import urlparse

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

_progress_store = {}
_lock = threading.Lock()


def _get_headers(url):
    headers = dict(BROWSER_HEADERS)
    if "bilibili.com" in url or "bilivideo.com" in url or "hdslb.com" in url:
        headers["Referer"] = "https://www.bilibili.com"
    if "douyin.com" in url or "zjcdn.com" in url:
        headers["Referer"] = "https://www.douyin.com"
    return headers


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


def get_progress(task_id):
    with _lock:
        return _progress_store.get(task_id, {"progress": 0, "status": "not_found"})


def _download_worker(url, filename, target_dir, task_id):
    if not url:
        with _lock:
            _progress_store[task_id] = {"progress": 0, "status": "error", "message": "下载链接为空"}
        return

    os.makedirs(target_dir, exist_ok=True)

    try:
        headers = _get_headers(url)

        with _lock:
            _progress_store[task_id] = {"progress": 0, "status": "downloading"}

        with requests.get(url, headers=headers, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            ext = _get_extension(url, r.headers.get("Content-Type", ""))
            save_name = f"{filename}{ext}"
            save_path = os.path.join(target_dir, save_name)

            downloaded = 0
            with open(save_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = downloaded / total
                        else:
                            pct = 0
                        with _lock:
                            _progress_store[task_id] = {
                                "progress": round(pct, 2),
                                "status": "downloading",
                                "downloaded": downloaded,
                                "total": total,
                            }

        with _lock:
            _progress_store[task_id] = {"progress": 1.0, "status": "done", "path": save_path}

    except Exception as e:
        with _lock:
            _progress_store[task_id] = {"progress": 0, "status": "error", "message": str(e)}


def start_download(url, filename, target_dir):
    task_id = str(len(_progress_store) + 1) + "_" + str(hash(url + filename))[-6:]
    thread = threading.Thread(target=_download_worker, args=(url, filename, target_dir, task_id), daemon=True)
    thread.start()
    return task_id
