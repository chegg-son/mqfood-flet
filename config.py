import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

DEFAULTS = {
    "base_url": "http://127.0.0.1:8001",
    "timeout_seconds": 15,
}


def _load():
    config = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config.update(json.load(f))
        except (OSError, json.JSONDecodeError):
            pass
    return config


CONFIG = _load()
BASE_URL = str(CONFIG.get("base_url", DEFAULTS["base_url"])).rstrip("/")
TIMEOUT = int(CONFIG.get("timeout_seconds", DEFAULTS["timeout_seconds"]))

# Tema — vibrant food app palette
PRIMARY = "#E53935"        # vivid red
PRIMARY_DARK = "#B71C1C"   # deep red
SECONDARY = "#FF7043"      # warm orange
ACCENT = "#FFC107"         # amber
BG_COLOR = "#FFF8F6"       # warm off-white
CARD_COLOR = "#FFFFFF"
TEXT_COLOR = "#1A1A1A"
SUBTEXT_COLOR = "#757575"
SURFACE_COLOR = "#FFECEB"  # very light red tint