import os
import re
from urllib.parse import urlparse


def sanitize_filename(name: str) -> str:
    if not name:
        return "untitled"
    illegal = '\\/:*?"<>|'
    for ch in illegal:
        name = name.replace(ch, '-')
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)
    name = name.replace('\n', '').replace('\r', '')
    return name[:120]


def get_extension(url: str, content_type: str = "") -> str:
    if content_type:
        mapping = {
            "video/mp4": ".mp4",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
        }
        for mime, ext in mapping.items():
            if mime in content_type:
                return ext
    path = urlparse(url).path
    _, ext = os.path.splitext(path)
    if ext and len(ext) <= 5:
        return ext.lower()
    return ".mp4"


def resolve_video_path(target_dir: str, title: str, ext: str = ".mp4") -> str:
    safe = sanitize_filename(title)
    path = os.path.join(target_dir, f"{safe}{ext}")
    if not os.path.exists(path):
        return path
    counter = 1
    while True:
        path = os.path.join(target_dir, f"{safe} ({counter}){ext}")
        if not os.path.exists(path):
            return path
        counter += 1


def resolve_album_path(target_dir: str, album_title: str) -> str:
    safe = sanitize_filename(album_title)
    path = os.path.join(target_dir, safe)
    if not os.path.exists(path):
        return path
    counter = 1
    while True:
        path = os.path.join(target_dir, f"{safe} ({counter})")
        if not os.path.exists(path):
            return path
        counter += 1


def image_filename(index: int, total: int, ext: str = ".jpg") -> str:
    width = len(str(total))
    return f"{str(index).zfill(width)}{ext}"
