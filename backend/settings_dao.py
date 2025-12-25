# backend/settings_dao.py

import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_FILE = os.path.join(BASE_DIR, "settings.json")


def get_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(settings: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)


# ---------------------------------------------------
# QR-SPECIFIC HELPERS
# ---------------------------------------------------

def get_qr_settings() -> dict:
    s = get_settings()
    return {
        "qr_text_prefix": s.get("qr_text_prefix", "Part"),
        "qr_start_counter": s.get("qr_start_counter", 1),
        "model_type": s.get("model_type", "RHD")
    }


def save_qr_settings(prefix: str, counter: int, model_type: str):
    s = get_settings()
    s.update({
        "qr_text_prefix": prefix,
        "qr_start_counter": counter,
        "model_type": model_type
    })
    save_settings(s)
