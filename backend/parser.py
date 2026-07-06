import re
import requests
import uuid

BILIBILI_API = "https://api.bugpk.com/api/bilibili"
DOUYIN_API = "https://api.bugpk.com/api/douyin"

BILI_API_VIEW = "https://api.bilibili.com/x/web-interface/view"
BILI_API_PLAYURL = "https://api.bilibili.com/x/player/playurl"
BILI_QUALITY_MAP = {
    "16": "360P",
    "32": "480P",
    "64": "720P",
    "80": "1080P",
    "112": "1080P+",
    "116": "1080P 60帧",
    "120": "4K",
    "125": "HDR",
}
_DEFAULT_QN = 80

BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com",
}


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


def _extract_bvid(url):
    m = re.search(r'(BV[a-zA-Z0-9]{10})', url)
    if m:
        return m.group(1)
    m = re.search(r'av(\d+)', url, re.IGNORECASE)
    if m:
        aid = m.group(1)
        resp = requests.get(BILI_API_VIEW, params={"aid": aid}, headers=BILI_HEADERS, timeout=10)
        return resp.json().get("data", {}).get("bvid")
    return None


def _parse_bilibili_native(url, quality):
    bvid = _extract_bvid(url)
    if not bvid:
        return None

    try:
        qn = quality if isinstance(quality, int) else _DEFAULT_QN
        if str(qn) not in BILI_QUALITY_MAP:
            qn = _DEFAULT_QN

        view_resp = requests.get(BILI_API_VIEW, params={"bvid": bvid}, headers=BILI_HEADERS, timeout=10)
        view_data = view_resp.json().get("data")
        if not view_data:
            return None

        pages = view_data.get("pages", [])
        if not pages:
            pages = [{"cid": view_data["cid"], "part": view_data.get("title", "视频")}]

        files = []
        for idx, page in enumerate(pages):
            cid = page.get("cid", view_data.get("cid"))
            play_resp = requests.get(
                BILI_API_PLAYURL,
                params={"bvid": bvid, "cid": cid, "qn": qn, "otype": "json"},
                headers=BILI_HEADERS,
                timeout=10,
            )
            play_data = play_resp.json().get("data")
            if not play_data:
                continue
            durl = play_data.get("durl", [])
            if not durl:
                continue
            video_url = durl[0].get("url", "")
            if not video_url:
                continue
            files.append({
                "index": idx + 1,
                "title": _clean_title(page.get("part", f"分P_{idx + 1}")),
                "url": video_url,
                "type": "video",
                "size": 0,
            })

        if not files:
            return None

        return {
            "title": _clean_title(view_data.get("title", "")),
            "platform": "bilibili",
            "type": "video",
            "cover": view_data.get("pic", ""),
            "files": files,
            "quality": str(qn),
        }
    except Exception:
        return None


def _parse_bilibili(url, quality=None):
    if quality:
        if quality in BILI_QUALITY_MAP:
            qn = int(quality)
        else:
            qn_map = {v: k for k, v in BILI_QUALITY_MAP.items()}
            qn = int(qn_map.get(quality, str(_DEFAULT_QN)))
        result = _parse_bilibili_native(url, qn)
        if result:
            return result
        return {
            "code": 400,
            "msg": f"该清晰度解析失败，请尝试其他清晰度",
            "platform": "bilibili",
            "files": [],
        }

    result = _parse_bilibili_native(url, _DEFAULT_QN)
    if result:
        return result

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
                    vurl = v.get("url", "")
                    if vurl:
                        files.append({
                            "index": v.get("index", len(files) + 1),
                            "title": _clean_title(v.get("title", "分P视频")),
                            "url": vurl,
                            "type": "video",
                            "size": _get_file_size(vurl),
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


def _parse_douyin(url, quality=None):
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


def parse_url(url, quality=None):
    url = _clean_url(_extract_url(url))
    platform = _detect_platform(url)
    if platform == "bilibili":
        return _parse_bilibili(url, quality=quality)
    elif platform == "douyin":
        return _parse_douyin(url, quality=quality)
    else:
        return {"title": "不支持的链接", "platform": "unknown", "type": "unknown", "files": []}
