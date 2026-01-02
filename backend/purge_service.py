# backend/purge_service.py
# ======================================================
# Purge Service (Production)
# ======================================================

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from backend.db import query
from backend.purge_settings import load_purge_settings

log = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# ======================================================
# PUBLIC ENTRY POINT
# ======================================================

def run_purge():
    """
    Main purge entry point.
    Safe to call from main.py / cron / systemd.
    """
    settings = load_purge_settings()
    now = datetime.now()

    sms_cutoff = now - timedelta(hours=settings["sms_sent_retention_hours"])
    qr_cutoff = now - timedelta(hours=settings["qr_retention_hours"])
    cycles_cutoff = now - timedelta(hours=settings["cycles_retention_hours"])

    log.warning(
        "🧹 Purge started | SMS=%dh | QR=%dh | Cycles=%dh",
        settings["sms_sent_retention_hours"],
        settings["qr_retention_hours"],
        settings["cycles_retention_hours"],
    )

    sms_deleted = _purge_sms_queue(sms_cutoff)
    qr_rows_deleted, qr_images_deleted = _purge_qr_codes_and_images(qr_cutoff)
    cycles_deleted = _purge_cycles(cycles_cutoff)

    log.warning(
        "✅ Purge completed | SMS=%d | QR rows=%d | QR images=%d | Cycles=%d (logs cascaded)",
        sms_deleted,
        qr_rows_deleted,
        qr_images_deleted,
        cycles_deleted,
    )

# ======================================================
# SMS QUEUE PURGE
# ======================================================

def _purge_sms_queue(cutoff: datetime) -> int:
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

        log.info("🗑 SMS purged: %d row(s)", count)
        return count

    except Exception:
        log.exception("❌ Failed to purge sms_queue")
        return 0

# ======================================================
# QR CODES + IMAGE FILES PURGE
# ======================================================

def _purge_qr_codes_and_images(cutoff: datetime) -> Tuple[int, int]:
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

        for row in rows:
            if _delete_qr_image(row.get("filename")):
                images_deleted += 1

        ids = [row["id"] for row in rows]
        placeholders = ",".join(["%s"] * len(ids))

        query(
            f"DELETE FROM qr_codes WHERE id IN ({placeholders})",
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
# CYCLES + PRINT LOG PURGE (CASCADE)
# ======================================================

def _purge_cycles(cutoff: datetime) -> int:
    try:
        rows = query(
            """
            SELECT id
            FROM cycles
            WHERE timestamp < %s
            """,
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )

        count = len(rows) if rows else 0
        if count == 0:
            log.info("ℹ No cycles to purge")
            return 0

        query(
            """
            DELETE FROM cycles
            WHERE timestamp < %s
            """,
            (cutoff.strftime("%Y-%m-%d %H:%M:%S"),),
        )

        log.info(
            "🗑 Cycles purged: %d row(s) (print logs cascaded)",
            count,
        )

        return count

    except Exception:
        log.exception("❌ Failed to purge cycles")
        return 0

# ======================================================
# FILE DELETE (SAFE)
# ======================================================

def _delete_qr_image(filename: Optional[str]) -> bool:
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
