import os
import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from parser import parse_url
from task_manager import create_task, get_task, get_all_tasks, delete_task, clear_tasks, TaskStatus
from config import get_download_dir, set_download_dir
from downloader import start_download

app = FastAPI(title="视频解析下载工具 V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    url: str
    quality: str = ""


class DownloadRequest(BaseModel):
    url: str
    title: str
    type: str = "video"
    cover: str = ""
    mode: str = "auto"
    threads: int = 4


class RetryRequest(BaseModel):
    task_id: str


class SetDirRequest(BaseModel):
    path: str


@app.post("/parse")
def parse(req: ParseRequest):
    quality = req.quality or None
    result = parse_url(req.url, quality=quality)
    if result.get("code") == 400:
        return result
    files = result.get("files", [])
    if not files:
        return {"code": 400, "msg": "解析失败，未找到可下载的资源", "data": {"task_list": []}}
    task_list = [
        {
            "index": f.get("index"),
            "title": f.get("title", "无标题"),
            "type": f.get("type", "video"),
            "cover": result.get("cover", ""),
            "download_url": f.get("url", ""),
            "size": f.get("size", 0),
        }
        for f in files
    ]
    return {
        "code": 200,
        "msg": "解析成功",
        "data": {
            "title": result.get("title", ""),
            "platform": result.get("platform", ""),
            "type": result.get("type", ""),
            "cover": result.get("cover", ""),
            "quality": result.get("quality", ""),
            "task_list": task_list,
        },
    }


@app.post("/download")
def download(req: DownloadRequest):
    target_dir = get_download_dir()
    task = create_task(
        title=req.title,
        url=req.url,
        type=req.type,
        cover=req.cover,
    )
    os.makedirs(target_dir, exist_ok=True)
    start_download(task, target_dir, mode=req.mode, threads=req.threads)
    return {"code": 200, "msg": "下载已开始", "data": {"task_id": task.task_id}}


@app.get("/tasks")
def tasks():
    all_tasks = get_all_tasks()
    return {
        "code": 200,
        "data": [
            {
                "task_id": t.task_id,
                "title": t.title,
                "type": t.type,
                "cover": t.cover,
                "status": t.status,
                "progress": t.progress,
                "file_path": t.file_path,
                "error": t.error,
            }
            for t in all_tasks
        ],
    }


@app.delete("/tasks")
def tasks_delete(scope: str = "finished"):
    clear_tasks(scope)
    return {"code": 200, "msg": "已清空"}


@app.get("/download/progress/{task_id}")
def download_progress(task_id: str):
    task = get_task(task_id)
    if not task:
        return {"code": 404, "data": {"progress": 0, "status": "not_found"}}
    return {
        "code": 200,
        "data": {
            "progress": task.progress,
            "status": task.status,
            "file_path": task.file_path,
            "error": task.error,
        },
    }


@app.post("/download/retry")
def download_retry(req: RetryRequest):
    task = get_task(req.task_id)
    if not task:
        return {"code": 404, "msg": "任务不存在"}
    if task.status != TaskStatus.FAILED:
        return {"code": 400, "msg": "只能重试失败的任务"}

    target_dir = get_download_dir()
    from task_manager import update_task

    update_task(task.task_id, status=TaskStatus.WAITING, progress=0, error=None, retry_count=0)
    start_download(task, target_dir)
    return {"code": 200, "msg": "已重新开始下载", "data": {"task_id": task.task_id}}


@app.delete("/download/{task_id}")
def download_delete(task_id: str):
    delete_task(task_id)
    return {"code": 200, "msg": "已删除"}


@app.get("/download_dir")
def get_dir():
    return {"code": 200, "path": get_download_dir()}


@app.post("/set_download_dir")
def set_dir(req: SetDirRequest):
    set_download_dir(req.path)
    return {"code": 200, "path": get_download_dir()}


BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.bilibili.com",
}


@app.get("/download/file/{task_id}")
def download_file(task_id: str):
    from download_manager import get_task

    task = get_task(task_id)
    if not task or not task.file_path or not os.path.isfile(task.file_path):
        return {"code": 404, "msg": "文件不存在"}
    ct = "image/png" if task.type == "image" else "video/mp4"
    return FileResponse(task.file_path, media_type=ct)


@app.get("/proxy/image")
def proxy_image(url: str = Query(...)):
    r = requests.get(url, headers=BROWSER_HEADERS, stream=True, timeout=15)
    ct = r.headers.get("Content-Type", "image/jpeg")
    return StreamingResponse(r.iter_content(chunk_size=65536), media_type=ct)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
