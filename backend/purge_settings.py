# backend/purge_settings.py
# ======================================================
# Purge Settings Loader
# ======================================================

import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PURGE_SETTINGS_FILE = os.path.join(BASE_DIR, "purge_settings.json")


DEFAULTS = {
    "sms_sent_retention_hours": 24,
    "qr_retention_hours": 24,
}


def load_purge_settings() -> dict:
    """
    Load purge settings from JSON.
    Falls back to defaults safely.
    """
    try:
        if not os.path.exists(PURGE_SETTINGS_FILE):
            return DEFAULTS.copy()

        with open(PURGE_SETTINGS_FILE, "r") as f:
            data = json.load(f)

        settings = DEFAULTS.copy()
        settings.update(
            {k: int(v) for k, v in data.items() if k in DEFAULTS}
        )

        # enforce minimum 1 hour
        settings["sms_sent_retention_hours"] = max(
            1, settings["sms_sent_retention_hours"]
        )
        settings["qr_retention_hours"] = max(
            1, settings["qr_retention_hours"]
        )

        return settings

    except Exception:
        return DEFAULTS.copy()
