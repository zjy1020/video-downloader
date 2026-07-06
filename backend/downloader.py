import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from task_manager import DownloadTask, TaskStatus, update_task
from naming import sanitize_filename, get_extension, resolve_video_path, resolve_album_path, image_filename

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


def _probe(url, headers):
    total_size = 0
    content_type = ""
    try:
        resp = _session.head(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            total_size = int(resp.headers.get("Content-Length", 0))
            content_type = resp.headers.get("Content-Type", "")
    except Exception:
        pass
    if total_size == 0:
        try:
            probe = _session.get(url, headers=headers, stream=True, timeout=10)
            total_size = int(probe.headers.get("Content-Length", 0))
            content_type = probe.headers.get("Content-Type", "")
            probe.close()
        except Exception:
            pass
    return total_size, content_type


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

        ext = get_extension(url, r.headers.get("Content-Type", ""))
        mode = "ab" if downloaded else "wb"
        with open(temp_path, mode) as f:
            for chunk in r.iter_content(chunk_size=1048576):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    pct = min(int(downloaded / total * 100), 100) if total > 0 else -1
                    update_task(task.task_id, progress=pct)
        return ext


def _download_parallel(task, url, headers, temp_path, total_size, parts, ext):
    part_dir = os.path.join(os.path.dirname(temp_path), f".{task.task_id}_parts")
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
            futures[pool.submit(_download_part, url, headers, s, e, pp)] = i

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
    return ext


def _resolve_final_path(task, target_dir, ext):
    if task.type == "image" and task.album_title:
        album_folder = resolve_album_path(target_dir, task.album_title)
        os.makedirs(album_folder, exist_ok=True)
        return os.path.join(album_folder, image_filename(task.index_in_album, task.total_in_album, ext))
    return resolve_video_path(target_dir, task.title, ext)


def _download_worker(task: DownloadTask, target_dir: str, mode: str = "auto", threads: int = 4):
    try:
        update_task(task.task_id, status=TaskStatus.DOWNLOADING, progress=0)

        headers = _get_headers(task.url)
        total_size, content_type = _probe(task.url, headers)

        os.makedirs(target_dir, exist_ok=True)
        temp_path = os.path.join(target_dir, f".{task.task_id}.download")

        if mode == "sequential":
            update_task(task.task_id, progress=1 if total_size > 0 else -1)
            ext = _download_sequential(task, task.url, headers, temp_path)

        elif mode == "parallel" and total_size > 0:
            ext = get_extension(task.url, content_type)
            try:
                _download_parallel(task, task.url, headers, temp_path, total_size, max(threads, 1), ext)
            except Exception:
                ext = _download_sequential(task, task.url, headers, temp_path)

        else:
            if total_size >= 5 * 1024 * 1024:
                ext = get_extension(task.url, content_type)
                try:
                    _download_parallel(task, task.url, headers, temp_path, total_size, 4, ext)
                except Exception:
                    ext = _download_sequential(task, task.url, headers, temp_path)
            elif total_size > 0:
                update_task(task.task_id, progress=1)
                ext = _download_sequential(task, task.url, headers, temp_path)
            else:
                update_task(task.task_id, progress=-1)
                ext = _download_sequential(task, task.url, headers, temp_path)

        final_path = _resolve_final_path(task, target_dir, ext)

        if os.path.exists(final_path):
            os.remove(final_path)
        os.rename(temp_path, final_path)

        update_task(task.task_id, status=TaskStatus.SUCCESS, progress=100, file_path=final_path)

    except Exception as e:
        if task.retry_count < task.max_retries:
            update_task(task.task_id, status=TaskStatus.WAITING, progress=0, error=None, retry_count=task.retry_count + 1)
            _executor.submit(_download_worker, task, target_dir)
        else:
            update_task(task.task_id, status=TaskStatus.FAILED, progress=0, error=str(e))
    finally:
        temp_path = os.path.join(target_dir, f".{task.task_id}.download")
        if os.path.exists(temp_path):
            os.remove(temp_path)


def start_download(task: DownloadTask, target_dir: str, mode: str = "auto", threads: int = 4):
    _executor.submit(_download_worker, task, target_dir, mode, threads)
    return task.task_id
