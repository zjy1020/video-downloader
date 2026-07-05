import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
from task_manager import DownloadTask, TaskStatus, update_task

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
}

_executor = ThreadPoolExecutor(max_workers=6)
_session = requests.Session()
_session.headers.update(BROWSER_HEADERS)


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


def _download_part(url, headers, start, end, part_path):
    part_headers = dict(headers)
    part_headers["Range"] = f"bytes={start}-{end}"
    with _session.get(url, headers=part_headers, stream=True, timeout=120) as r:
        with open(part_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1048576):
                if chunk:
                    f.write(chunk)


def _download_sequential(task, url, headers, temp_path):
    resume_headers = dict(headers)
    downloaded = 0
    if os.path.exists(temp_path):
        downloaded = os.path.getsize(temp_path)
        if downloaded > 0:
            resume_headers["Range"] = f"bytes={downloaded}-"

    with _session.get(url, headers=resume_headers, stream=True, timeout=120) as r:
        if downloaded > 0 and r.status_code == 206:
            total = int(r.headers.get("Content-Length", 0)) + downloaded
        else:
            r.raise_for_status()
            total = int(r.headers.get("Content-Length", 0))
            downloaded = 0

        ext = _get_extension(url, r.headers.get("Content-Type", ""))
        mode = "ab" if downloaded else "wb"
        with open(temp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=1048576):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = min(int(downloaded / total * 100), 100) if total > 0 else -1
                    update_task(task.task_id, progress=pct)
        return ext


def _download_worker(task: DownloadTask, target_dir: str):
    try:
        update_task(task.task_id, status=TaskStatus.DOWNLOADING, progress=0)

        headers = _get_headers(task.url)
        base_name = _sanitize_filename(task.title)
        os.makedirs(target_dir, exist_ok=True)
        temp_path = os.path.join(target_dir, f"{base_name}.download")

        total_size = 0
        try:
            resp = _session.head(task.url, headers=headers, timeout=10)
            if resp.status_code == 200:
                total_size = int(resp.headers.get("Content-Length", 0))
        except Exception:
            pass

        if total_size == 0:
            try:
                probe = _session.get(task.url, headers=headers, stream=True, timeout=10)
                total_size = int(probe.headers.get("Content-Length", 0))
                probe.close()
            except Exception:
                pass

        if total_size >= 5 * 1024 * 1024:
            ext = _get_extension(task.url, "")
            try:
                parts = 4
                part_dir = os.path.join(target_dir, f"{base_name}_parts")
                os.makedirs(part_dir, exist_ok=True)
                part_size = total_size // parts

                ranges = []
                for i in range(parts):
                    start = i * part_size
                    end = (start + part_size - 1) if i < parts - 1 else ""
                    ranges.append((start, end))

                part_paths = []
                with ThreadPoolExecutor(max_workers=parts) as pool:
                    futures = {}
                    for i, (s, e) in enumerate(ranges):
                        pp = os.path.join(part_dir, f"part_{i}")
                        part_paths.append(pp)
                        futures[pool.submit(_download_part, task.url, headers, s, e, pp)] = i

                    done = 0
                    for f in as_completed(futures):
                        f.result()
                        done += 1
                        update_task(task.task_id, progress=int(done / parts * 100))

                with open(temp_path, "wb") as out:
                    for pp in sorted(part_paths):
                        with open(pp, "rb") as pf:
                            out.write(pf.read())

                for pp in part_paths:
                    os.remove(pp)
                os.rmdir(part_dir)
            except Exception:
                ext = _download_sequential(task, task.url, headers, temp_path)
        elif total_size > 0:
            update_task(task.task_id, progress=1)
            ext = _download_sequential(task, task.url, headers, temp_path)
        else:
            update_task(task.task_id, progress=-1)
            ext = _download_sequential(task, task.url, headers, temp_path)

        save_path = os.path.join(target_dir, f"{base_name}{ext}")

        counter = 1
        final_path = save_path
        while os.path.exists(final_path):
            base, ext = os.path.splitext(save_path)
            final_path = f"{base}_{counter}{ext}"
            counter += 1
        os.rename(temp_path, final_path)

        update_task(task.task_id, status=TaskStatus.SUCCESS, progress=100, file_path=final_path)

    except Exception as e:
        if task.retry_count < task.max_retries:
            update_task(task.task_id, status=TaskStatus.WAITING, progress=0, error=None, retry_count=task.retry_count + 1)
            _executor.submit(_download_worker, task, target_dir)
        else:
            update_task(task.task_id, status=TaskStatus.FAILED, progress=0, error=str(e))


def start_download(task: DownloadTask, target_dir: str):
    _executor.submit(_download_worker, task, target_dir)
    return task.task_id
