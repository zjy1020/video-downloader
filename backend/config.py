import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "download_config.json")
DEFAULT_DIR = os.path.join(os.path.dirname(__file__), "downloads")


def _load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_download_dir():
    cfg = _load_config()
    return cfg.get("download_dir", DEFAULT_DIR)


def set_download_dir(path):
    _save_config({"download_dir": path})
