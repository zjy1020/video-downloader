import requests
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from parser import parse_url
from downloader import start_download, get_progress
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
    task_id = start_download(req.url, req.filename, target_dir)
    return {"code": 200, "msg": "下载已开始", "data": {"task_id": task_id}}


@app.get("/download/progress/{task_id}")
def download_progress(task_id: str):
    data = get_progress(task_id)
    return {"code": 200, "data": data}


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


@app.get("/proxy/image")
def proxy_image(url: str = Query(...)):
    r = requests.get(url, headers=BROWSER_HEADERS, stream=True, timeout=15)
    ct = r.headers.get("Content-Type", "image/jpeg")
    return StreamingResponse(r.iter_content(chunk_size=65536), media_type=ct)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
