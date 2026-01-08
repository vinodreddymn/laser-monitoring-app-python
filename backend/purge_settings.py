# backend/purge_settings.py
# ======================================================
# Purge Settings Loader (Single Source of Truth)
# ======================================================

import json
import os
import logging

log = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PURGE_SETTINGS_FILE = os.path.join(BASE_DIR, "config.json")

DEFAULTS = {
    "sms_sent_retention_hours": 24,
    "qr_retention_hours": 24,
    "cycles_retention_hours": 48,
}


def load_purge_settings() -> dict:
    """
    Load purge settings from config.json.
    Falls back to safe defaults.
    Enforces minimum 1 hour.
    """
    try:
        if not os.path.exists(PURGE_SETTINGS_FILE):
            log.warning("config.json not found → using defaults")
            return DEFAULTS.copy()

        with open(PURGE_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        purge_data = data.get("purge_settings", {})

        settings = DEFAULTS.copy()

        for key in settings:
            if key in purge_data:
                settings[key] = max(1, int(purge_data[key]))

        return settings

    except Exception:
        log.exception("Failed to load purge settings → using defaults")
        return DEFAULTS.copy()
