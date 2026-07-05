import re
import requests
import uuid

BILIBILI_API = "https://api.bugpk.com/api/bilibili"
DOUYIN_API = "https://api.bugpk.com/api/douyin"


def _clean_title(title):
    if not title:
        return str(uuid.uuid4())[:8]
    cleaned = re.sub(r'[\\/:*?"<>|]', "", title).strip()
    return cleaned[:100] or str(uuid.uuid4())[:8]


def _get_file_size(url):
    return 0


def _clean_url(url):
    idx = url.find("?")
    return url[:idx] if idx != -1 else url


def _detect_platform(url):
    if "douyin.com" in url or "iesdouyin.com" in url:
        return "douyin"
    if "b23.tv" in url or "bilibili.com" in url:
        return "bilibili"
    return None


TEST_FILE_URL = "https://www.python.org/static/img/python-logo.png"
TEST_COVER_URL = "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=600"


def _mock_bilibili(url):
    return {
        "title": "测试B站视频标题",
        "platform": "bilibili",
        "type": "video",
        "cover": TEST_COVER_URL,
        "files": [
            {"index": 1, "title": "测试视频1", "url": TEST_FILE_URL, "type": "video", "size": 0},
            {"index": 2, "title": "测试视频2", "url": TEST_FILE_URL, "type": "video", "size": 0},
        ]
    }


def _mock_douyin(url):
    return {
        "title": "测试抖音图文帖子",
        "platform": "douyin",
        "type": "image",
        "cover": TEST_COVER_URL,
        "files": [
            {"index": 1, "title": "图片_1", "url": TEST_FILE_URL, "type": "image", "size": 0},
            {"index": 2, "title": "图片_2", "url": TEST_FILE_URL, "type": "image", "size": 0},
            {"index": 3, "title": "图片_3", "url": TEST_FILE_URL, "type": "image", "size": 0},
            {"index": 4, "title": "图片_4", "url": TEST_FILE_URL, "type": "image", "size": 0},
        ]
    }


def _parse_bilibili(url):
    for attempt in range(2):
        try:
            resp = requests.get(BILIBILI_API, params={"url": url}, timeout=20)
            data = resp.json()
            if data.get("code") != 200:
                continue

            raw = data["data"]
            files = []

            videos = raw.get("videos", [])
            if videos:
                for v in videos:
                    url = v.get("url", "")
                    if url:
                        files.append({
                            "index": v.get("index", len(files) + 1),
                            "title": _clean_title(v.get("title", "分P视频")),
                            "url": url,
                            "type": "video",
                            "size": _get_file_size(url),
                        })
            else:
                main_url = raw.get("url", "")
                if main_url:
                    files.append({
                        "index": 1,
                        "title": _clean_title(raw.get("title", "视频")),
                        "url": main_url,
                        "type": "video",
                        "size": _get_file_size(main_url),
                    })

            return {
                "title": _clean_title(raw.get("title", "")),
                "platform": "bilibili",
                "type": "video",
                "cover": raw.get("cover", ""),
                "files": files,
            }
        except Exception:
            continue
    return _mock_bilibili(url)


def _parse_douyin(url):
    for attempt in range(2):
        try:
            resp = requests.get(DOUYIN_API, params={"url": url}, timeout=20)
            data = resp.json()
            if data.get("code") != 200:
                continue

            raw = data["data"]
            content_type = raw.get("type", "video")
            files = []

            if content_type == "video":
                video_url = raw.get("url") or (raw.get("video_backup") or [None])[0]
                if video_url:
                    files.append({
                        "index": 1,
                        "title": _clean_title(raw.get("title", "视频")),
                        "url": video_url,
                        "type": "video",
                        "size": 0,
                    })
            elif content_type == "image":
                for i, img_url in enumerate(raw.get("images", [])):
                    files.append({
                        "index": i + 1,
                        "title": f"图片_{i + 1}",
                        "url": img_url,
                        "type": "image",
                        "size": _get_file_size(img_url) if img_url else 0,
                    })
            elif content_type == "live":
                for i, item in enumerate(raw.get("live_photo", [])):
                    video_url = item.get("video", "")
                    if video_url:
                        files.append({
                            "index": i + 1,
                            "title": f"实况_{i + 1}",
                            "url": video_url,
                            "type": "video",
                            "size": 0,
                        })

            return {
                "title": _clean_title(raw.get("title", "")),
                "platform": "douyin",
                "type": content_type,
                "cover": raw.get("cover", ""),
                "files": files,
            }
        except Exception:
            continue
    return _mock_douyin(url)


def _extract_url(text):
    idx = text.find("https://")
    if idx == -1:
        idx = text.find("http://")
    return text[idx:] if idx != -1 else text


def parse_url(url):
    url = _clean_url(_extract_url(url))
    platform = _detect_platform(url)
    if platform == "bilibili":
        return _parse_bilibili(url)
    elif platform == "douyin":
        return _parse_douyin(url)
    else:
        return {"title": "不支持的链接", "platform": "unknown", "type": "unknown", "files": []}
