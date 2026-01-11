# ======================================================
# Purge Service (Production with Archival)
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
    Archive → Verify → Delete
    """
    settings = load_purge_settings()
    now = datetime.now()

    purge_batch_id = now.strftime("%Y%m%d%H%M%S")

    sms_cutoff = now - timedelta(hours=settings["sms_sent_retention_hours"])
    qr_cutoff = now - timedelta(hours=settings["qr_retention_hours"])
    cycles_cutoff = now - timedelta(hours=settings["cycles_retention_hours"])

    log.warning(
        "🧹 Purge started | batch=%s | SMS=%dh | QR=%dh | Cycles=%dh",
        purge_batch_id,
        settings["sms_sent_retention_hours"],
        settings["qr_retention_hours"],
        settings["cycles_retention_hours"],
    )

    sms_deleted = _purge_sms_queue(sms_cutoff, purge_batch_id)
    qr_rows_deleted, qr_images_deleted = _purge_qr_codes_and_images(qr_cutoff, purge_batch_id)
    cycles_deleted = _purge_cycles_and_logs(cycles_cutoff, purge_batch_id)

    log.warning(
        "✅ Purge completed | SMS=%d | QR rows=%d | QR images=%d | Cycles=%d",
        sms_deleted,
        qr_rows_deleted,
        qr_images_deleted,
        cycles_deleted,
    )


# ======================================================
# SMS QUEUE PURGE (ARCHIVE FIRST)
# ======================================================

def _purge_sms_queue(cutoff: datetime, batch_id: str) -> int:
    try:
        rows = query(
            """
            SELECT *
            FROM sms_queue
            WHERE status = 'sent'
              AND timestamp < %s
            """,
            (cutoff,),
        )

        if not rows:
            log.info("ℹ No SENT SMS to purge")
            return 0

        for r in rows:
            query(
                """
                INSERT INTO sms_queue_archive
                (timestamp, phone, name, message, status, retry_count, last_error,
                 archived_at, purge_batch_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    r["timestamp"],
                    r["phone"],
                    r["name"],
                    r["message"],
                    r["status"],
                    r["retry_count"],
                    r["last_error"],
                    datetime.now(),
                    batch_id,
                ),
            )

        query(
            """
            DELETE FROM sms_queue
            WHERE status = 'sent'
              AND timestamp < %s
            """,
            (cutoff,),
        )

        log.info("🗄 SMS archived & purged: %d row(s)", len(rows))
        return len(rows)

    except Exception:
        log.exception("❌ Failed to archive/purge sms_queue")
        return 0


# ======================================================
# QR CODES + IMAGE FILES PURGE
# ======================================================

def _purge_qr_codes_and_images(cutoff: datetime, batch_id: str) -> Tuple[int, int]:
    try:
        rows = query(
            """
            SELECT *
            FROM qr_codes
            WHERE created_at < %s
            """,
            (cutoff,),
        )

        if not rows:
            log.info("ℹ No QR codes to purge")
            return 0, 0

        images_deleted = 0

        for r in rows:
            # Archive metadata (not images)
            query(
                """
                INSERT INTO qr_codes_archive
                (qr_data, created_at, filename, archived_at, purge_batch_id)
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    r["qr_data"],
                    r["created_at"],
                    r["filename"],
                    datetime.now(),
                    batch_id,
                ),
            )

            if _delete_qr_image(r.get("filename")):
                images_deleted += 1

        ids = [r["id"] for r in rows]
        placeholders = ",".join(["%s"] * len(ids))

        query(
            f"DELETE FROM qr_codes WHERE id IN ({placeholders})",
            tuple(ids),
        )

        log.info(
            "🗄 QR codes archived & purged: %d row(s), %d image(s)",
            len(ids),
            images_deleted,
        )

        return len(ids), images_deleted

    except Exception:
        log.exception("❌ Failed to archive/purge qr_codes")
        return 0, 0


# ======================================================
# CYCLES + PRINT LOGS (ARCHIVE BOTH)
# ======================================================

def _purge_cycles_and_logs(cutoff: datetime, batch_id: str) -> int:
    try:
        cycles = query(
            """
            SELECT *
            FROM cycles
            WHERE timestamp < %s
            """,
            (cutoff,),
        )

        if not cycles:
            log.info("ℹ No cycles to purge")
            return 0

        cycle_ids = [c["id"] for c in cycles]

        # ---- Archive cycles ----
        for c in cycles:
            query(
                """
                INSERT INTO cycles_archive
                (timestamp, model_id, model_name, model_type,
                peak_height, pass_fail, qr_code, printed,
                archived_at, purge_batch_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    c["timestamp"],
                    c["model_id"],
                    c["model_name"],
                    c["model_type"],     # ✅ FIXED
                    c["peak_height"],
                    c["pass_fail"],
                    c["qr_code"],
                    c["printed"],
                    datetime.now(),
                    batch_id,
                ),
            )


        # ---- Archive print logs linked to cycles ----
        placeholders = ",".join(["%s"] * len(cycle_ids))
        logs = query(
            f"""
            SELECT *
            FROM cycle_print_log
            WHERE cycle_id IN ({placeholders})
            """,
            tuple(cycle_ids),
        )

        for l in logs or []:
            query(
                """
                INSERT INTO cycle_print_log_archive
                (cycle_id, print_type, printed_at, printed_by, reason,
                 archived_at, purge_batch_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    l["cycle_id"],
                    l["print_type"],
                    l["printed_at"],
                    l["printed_by"],
                    l["reason"],
                    datetime.now(),
                    batch_id,
                ),
            )

        # ---- Delete cycles (logs cascade or already archived) ----
        query(
            """
            DELETE FROM cycles
            WHERE timestamp < %s
            """,
            (cutoff,),
        )

        log.info(
            "🗄 Cycles & print logs archived and purged: %d cycle(s)",
            len(cycles),
        )

        return len(cycles)

    except Exception:
        log.exception("❌ Failed to archive/purge cycles")
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
