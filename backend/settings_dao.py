# backend/settings_dao.py

import json
import os
import logging

log = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SETTINGS_FILE = os.path.join(BASE_DIR, "config.json")


def get_settings() -> dict:
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("qr_settings", {})
    except Exception:
        return {}


def save_settings(settings: dict):
    # Load full config
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    # Update qr_settings
    config["qr_settings"] = settings

    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    log.info("Saved QR settings: %s", settings)


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
