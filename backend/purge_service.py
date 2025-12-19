# backend/purge_service.py
# ======================================================
# Purge Service (Production)
#
# - Deletes SENT SMS older than user-defined hours
# - Deletes QR codes + QR image files older than user-defined hours
# - Intervals are loaded from purge_settings.json
#
# Safe to call from main.py
# ======================================================

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from backend.db import query

log = logging.getLogger(__name__)

# ======================================================
# PATHS & DEFAULTS
# ======================================================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PURGE_SETTINGS_FILE = os.path.join(BASE_DIR, "purge_settings.json")

DEFAULT_SETTINGS = {
    "sms_sent_retention_hours": 24,
    "qr_retention_hours": 24,
}

# ======================================================
# SETTINGS LOADER
# ======================================================

def _load_purge_settings() -> dict:
    """
    Load purge settings from purge_settings.json.
    Falls back to safe defaults.
    """
    try:
        if not os.path.exists(PURGE_SETTINGS_FILE):
            log.warning("purge_settings.json not found → using defaults")
            return DEFAULT_SETTINGS.copy()

        with open(PURGE_SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        settings = DEFAULT_SETTINGS.copy()
        for key in settings:
            if key in data:
                settings[key] = max(1, int(data[key]))

        return settings

    except Exception:
        log.exception("Failed to load purge_settings.json → using defaults")
        return DEFAULT_SETTINGS.copy()

# ======================================================
# PUBLIC ENTRY POINT
# ======================================================

def run_purge():
    """
    Main purge entry point.
    Call this safely from main.py.
    """
    settings = _load_purge_settings()

    sms_hours = settings["sms_sent_retention_hours"]
    qr_hours = settings["qr_retention_hours"]

    sms_cutoff = datetime.now() - timedelta(hours=sms_hours)
    qr_cutoff = datetime.now() - timedelta(hours=qr_hours)

    log.warning(
        "🧹 Purge started | SMS retention=%dh | QR retention=%dh",
        sms_hours,
        qr_hours,
    )

    sms_deleted = _purge_sms_queue(sms_cutoff)
    qr_rows_deleted, qr_images_deleted = _purge_qr_codes_and_images(qr_cutoff)

    log.warning(
        "✅ Purge completed | SMS deleted=%d | QR rows=%d | QR images=%d",
        sms_deleted,
        qr_rows_deleted,
        qr_images_deleted,
    )

# ======================================================
# SMS QUEUE PURGE
# ======================================================

def _purge_sms_queue(cutoff: datetime) -> int:
    """
    Delete only SENT SMS older than cutoff.
    """
    try:
        rows = query(
            """
            SELECT id
            FROM sms_queue
            WHERE status = 'sent'
              AND timestamp < %s
            """,
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )

        count = len(rows) if rows else 0
        if count == 0:
            log.info("ℹ No SENT SMS to purge")
            return 0

        query(
            """
            DELETE FROM sms_queue
            WHERE status = 'sent'
              AND timestamp < %s
            """,
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )

        log.info("🗑 SMS queue purged: %d row(s)", count)
        return count

    except Exception:
        log.exception("❌ Failed to purge sms_queue")
        return 0

# ======================================================
# QR CODES + IMAGE FILES PURGE
# ======================================================

def _purge_qr_codes_and_images(cutoff: datetime) -> Tuple[int, int]:
    """
    Delete QR DB rows and corresponding image files older than cutoff.
    """
    try:
        rows = query(
            """
            SELECT id, filename
            FROM qr_codes
            WHERE created_at < %s
            """,
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )

        if not rows:
            log.info("ℹ No QR codes to purge")
            return 0, 0

        images_deleted = 0

        # ---- delete files first ----
        for row in rows:
            if _delete_qr_image(row.get("filename")):
                images_deleted += 1

        # ---- delete DB rows ----
        ids = [row["id"] for row in rows]
        placeholders = ",".join(["%s"] * len(ids))

        query(
            f"""
            DELETE FROM qr_codes
            WHERE id IN ({placeholders})
            """,
            tuple(ids),
        )

        log.info(
            "🗑 QR codes purged: %d row(s), %d image(s)",
            len(ids),
            images_deleted,
        )

        return len(ids), images_deleted

    except Exception:
        log.exception("❌ Failed to purge qr_codes")
        return 0, 0

# ======================================================
# FILE DELETE (SAFE)
# ======================================================

def _delete_qr_image(filename: Optional[str]) -> bool:
    """
    Deletes a QR image file.
    Returns True if a file was actually deleted.
    """
    if not filename:
        return False

    try:
        path = filename
        if not os.path.isabs(path):
            path = os.path.join(BASE_DIR, path)

        if os.path.exists(path):
            os.remove(path)
            log.debug("🗑 Deleted QR image: %s", path)
            return True

    except Exception:
        log.exception("❌ Failed to delete QR image: %s", filename)

    return False
