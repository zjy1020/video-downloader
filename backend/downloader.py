import os
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from task_manager import DownloadTask, TaskStatus, update_task

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

_executor = ThreadPoolExecutor(max_workers=3)


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


def _sanitize_filename(name):
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    return name.strip()[:120]


def _download_worker(task: DownloadTask, target_dir: str):
    try:
        update_task(task.task_id, status=TaskStatus.DOWNLOADING, progress=0)

        headers = _get_headers(task.url)
        base_name = _sanitize_filename(task.title)
        os.makedirs(target_dir, exist_ok=True)
        temp_path = os.path.join(target_dir, f"{base_name}.download")

        downloaded = 0
        resume = False
        if os.path.exists(temp_path):
            downloaded = os.path.getsize(temp_path)
            if downloaded > 0:
                resume = True
                headers["Range"] = f"bytes={downloaded}-"

        with requests.get(task.url, headers=headers, stream=True, timeout=120) as r:
            if resume and r.status_code == 206:
                total = int(r.headers.get("Content-Length", 0)) + downloaded
            else:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length", 0))
                downloaded = 0

            ext = _get_extension(task.url, r.headers.get("Content-Type", ""))
            save_path = os.path.join(target_dir, f"{base_name}{ext}")

            mode = "ab" if resume else "wb"
            with open(temp_path, mode) as f:
                for chunk in r.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = min(int(downloaded / total * 100), 100)
                        else:
                            pct = 0
                        update_task(task.task_id, progress=pct)

        if os.path.exists(temp_path):
            counter = 1
            final_path = save_path
            while os.path.exists(final_path):
                base, ext = os.path.splitext(save_path)
                final_path = f"{base}_{counter}{ext}"
                counter += 1
            os.rename(temp_path, final_path)
            save_path = final_path

        update_task(task.task_id, status=TaskStatus.SUCCESS, progress=100, file_path=save_path)

    except Exception as e:
        if task.retry_count < task.max_retries:
            update_task(task.task_id, status=TaskStatus.WAITING, progress=0, error=None, retry_count=task.retry_count + 1)
            _executor.submit(_download_worker, task, target_dir)
        else:
            update_task(task.task_id, status=TaskStatus.FAILED, progress=0, error=str(e))


def start_download(task: DownloadTask, target_dir: str):
    _executor.submit(_download_worker, task, target_dir)
    return task.task_id
