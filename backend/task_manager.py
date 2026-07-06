import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


TASKS_FILE = os.path.join(os.path.dirname(__file__), "tasks.json")


class TaskStatus:
    WAITING = "waiting"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class DownloadTask:
    task_id: str
    title: str
    url: str
    type: str
    cover: str = ""
    status: str = TaskStatus.WAITING
    progress: int = 0
    file_path: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 1
    platform: str = "unknown"
    album_title: str = ""
    index_in_album: int = 0
    total_in_album: int = 0
    created_at: float = field(default_factory=time.time)
    downloaded_bytes: int = 0
    total_bytes: int = 0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


_task_store: dict[str, DownloadTask] = {}
_task_lock = threading.RLock()


def _save_tasks():
    with _task_lock:
        data = [
            {
                "task_id": t.task_id,
                "title": t.title,
                "url": t.url,
                "type": t.type,
                "cover": t.cover,
                "status": t.status,
                "progress": t.progress,
                "file_path": t.file_path,
                "error": t.error,
                "retry_count": t.retry_count,
                "max_retries": t.max_retries,
                "platform": t.platform,
                "album_title": t.album_title,
                "index_in_album": t.index_in_album,
                "total_in_album": t.total_in_album,
                "created_at": t.created_at,
                "downloaded_bytes": t.downloaded_bytes,
                "total_bytes": t.total_bytes,
                "started_at": t.started_at,
                "finished_at": t.finished_at,
            }
            for t in _task_store.values()
        ]
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_tasks():
    if not os.path.exists(TASKS_FILE):
        return
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    with _task_lock:
        for item in data:
            task = DownloadTask(**item)
            _task_store[task.task_id] = task


def create_task(title: str, url: str, type: str, cover: str = "", platform: str = "unknown", album_title: str = "", index_in_album: int = 0, total_in_album: int = 0) -> DownloadTask:
    task_id = str(uuid.uuid4())[:8]
    task = DownloadTask(
        task_id=task_id,
        title=title,
        url=url,
        type=type,
        cover=cover,
        platform=platform,
        album_title=album_title,
        index_in_album=index_in_album,
        total_in_album=total_in_album,
    )
    with _task_lock:
        _task_store[task_id] = task
    _save_tasks()
    return task


def get_task(task_id: str) -> Optional[DownloadTask]:
    with _task_lock:
        return _task_store.get(task_id)


def get_all_tasks() -> list[DownloadTask]:
    with _task_lock:
        tasks = list(_task_store.values())
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        return tasks


def update_task(task_id: str, **kwargs):
    with _task_lock:
        task = _task_store.get(task_id)
        if task:
            for k, v in kwargs.items():
                setattr(task, k, v)
            if "status" in kwargs:
                _save_tasks()


def delete_task(task_id: str):
    with _task_lock:
        _task_store.pop(task_id, None)
    _save_tasks()


def clear_tasks(scope: str = "all"):
    with _task_lock:
        if scope == "all":
            _task_store.clear()
        elif scope == "finished":
            to_delete = [tid for tid, t in _task_store.items() if t.status in (TaskStatus.SUCCESS, TaskStatus.FAILED)]
            for tid in to_delete:
                del _task_store[tid]
        elif scope == "failed":
            to_delete = [tid for tid, t in _task_store.items() if t.status == TaskStatus.FAILED]
            for tid in to_delete:
                del _task_store[tid]
    _save_tasks()


_load_tasks()
