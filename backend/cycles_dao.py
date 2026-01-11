# ======================================================
# backend/cycles_dao.py
# Pneumatic Laser QC System
#
# SINGLE SOURCE OF TRUTH – CYCLES DATA ACCESS
#
# Responsibilities:
# - Persist detected cycles (live)
# - Maintain active model cache (watchdog-driven)
# - Serve dashboard / UI queries
# - Serve pending QR print queue
# - Support live + archived reprints
# - Mark printed cycles safely
# - Maintain full print audit trail
# ======================================================

from datetime import datetime
import logging
from typing import List, Optional, Dict

from backend.db import query
from backend.model_watchdog import get_cached_model, register_listener

log = logging.getLogger(__name__)

# ======================================================
# ACTIVE MODEL CACHE (HOT PATH OPTIMIZATION)
# ======================================================

ACTIVE_MODEL_CACHE: Dict[str, Optional[object]] = {
    "id": None,
    "name": None,
    "model_type": None,
    "lower_limit": 0.0,
    "upper_limit": 100.0,
}

# ======================================================
# INTERNAL HELPERS
# ======================================================

def _format_timestamp(iso_string: Optional[str]) -> str:
    """
    Convert ISO timestamp → MySQL DATETIME safely.
    """
    if not iso_string:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        log.warning("Invalid timestamp '%s', using now()", iso_string)
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _update_local_cache(model: dict):
    """
    Watchdog callback – keeps cycle logging DB-free.
    """
    if not model:
        return

    try:
        ACTIVE_MODEL_CACHE.update(
            {
                "id": model.get("id"),
                "name": model.get("name"),
                "model_type": model.get("model_type"),
                "lower_limit": float(
                    model.get("lower_limit", model.get("lower", 0.0))
                ),
                "upper_limit": float(
                    model.get("upper_limit", model.get("upper", 100.0))
                ),
            }
        )

        log.info("Active model cache updated → %s", ACTIVE_MODEL_CACHE)

    except Exception:
        log.exception("Failed to update active model cache")


# ======================================================
# WATCHDOG REGISTRATION
# ======================================================

register_listener(_update_local_cache)

try:
    _update_local_cache(get_cached_model())
except Exception:
    pass


# ======================================================
# CYCLE PERSISTENCE (LIVE)
# ======================================================

def log_cycle(cycle: dict) -> int:
    """
    Persist a detected cycle into `cycles`.

    REQUIRED FIELDS (from service):
    - timestamp
    - peak_height
    - pass_fail
    - qr_text (PASS only)
    - model_type
    """

    formatted_ts = _format_timestamp(cycle.get("timestamp"))

    model_id = ACTIVE_MODEL_CACHE.get("id", cycle.get("model_id"))
    model_name = (
        ACTIVE_MODEL_CACHE.get("name")
        or cycle.get("model_name")
        or "UNKNOWN"
    )
    model_type = (
        ACTIVE_MODEL_CACHE.get("model_type")
        or cycle.get("model_type")
    )

    cycle_id = query(
        """
        INSERT INTO cycles
            (timestamp, model_id, model_name, model_type,
             peak_height, pass_fail, qr_code)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            formatted_ts,
            model_id,
            model_name,
            model_type,
            cycle.get("peak_height"),
            cycle.get("pass_fail"),
            cycle.get("qr_text"),
        ),
    )

    log.info(
        "Cycle logged | id=%s | model=%s | type=%s | peak=%.2f | result=%s",
        cycle_id,
        model_name,
        model_type,
        cycle.get("peak_height", 0.0),
        cycle.get("pass_fail"),
    )

    return cycle_id


# ======================================================
# DASHBOARD / HISTORY
# ======================================================

def get_cycles(limit: int = 50) -> List[dict]:
    """
    Recent cycles for dashboards.
    """
    return query(
        """
        SELECT *
        FROM cycles
        ORDER BY id DESC
        LIMIT %s
        """,
        (limit,),
    )


# ======================================================
# PENDING QR PRINT QUEUE (FIRST PRINT)
# ======================================================

def get_pending_qr_cycles(limit: int = 100) -> List[dict]:
    """
    Cycles that have QR generated but not yet printed.
    """
    return query(
        """
        SELECT
            c.id,
            c.timestamp,
            c.model_name,
            c.model_type,
            c.peak_height,
            c.pass_fail,
            c.qr_code,
            q.filename AS qr_image_path
        FROM cycles c
        JOIN qr_codes q
          ON q.qr_data = c.qr_code
        WHERE c.qr_code IS NOT NULL
          AND c.printed = 0
        ORDER BY c.timestamp ASC
        LIMIT %s
        """,
        (limit,),
    )


# ======================================================
# SEARCH BY QR (LIVE + ARCHIVE)
# ======================================================

def get_cycle_by_qr_code(qr_code: str) -> Optional[dict]:
    """
    Fetch cycle by QR code.
    Search order:
      1. cycles
      2. cycles_archive
    """

    # ---------- LIVE ----------
    rows = query(
        """
        SELECT
            c.id            AS cycle_id,
            c.timestamp,
            c.model_id,
            c.model_name,
            c.model_type,
            c.peak_height,
            c.pass_fail,
            c.qr_code,
            c.printed,
            q.filename      AS qr_image_path
        FROM cycles c
        LEFT JOIN qr_codes q
            ON q.qr_data = c.qr_code
        WHERE c.qr_code = %s
        ORDER BY c.timestamp DESC
        LIMIT 1
        """,
        (qr_code,),
    )

    if rows:
        row = rows[0]
        row["source"] = "live"
        return row

    # ---------- ARCHIVE ----------
    rows = query(
        """
        SELECT
            ca.id           AS cycle_id,
            ca.timestamp,
            ca.model_id,
            ca.model_name,
            ca.model_type,
            ca.peak_height,
            ca.pass_fail,
            ca.qr_code,
            ca.printed,
            qa.filename     AS qr_image_path
        FROM cycles_archive ca
        LEFT JOIN qr_codes_archive qa
            ON qa.qr_data = ca.qr_code
        WHERE ca.qr_code = %s
        ORDER BY ca.timestamp DESC
        LIMIT 1
        """,
        (qr_code,),
    )

    if rows:
        row = rows[0]
        row["source"] = "archive"
        return row

    return None


# ======================================================
# PRINT STATE MANAGEMENT
# ======================================================

def mark_printed(cycle_id: int) -> int:
    """
    Mark cycle as printed.
    Safe + idempotent.
    """
    return query(
        """
        UPDATE cycles
        SET printed = 1
        WHERE id = %s
          AND printed = 0
        """,
        (cycle_id,),
    )


def mark_printed_bulk(cycle_ids: List[int]) -> int:
    """
    Bulk mark cycles as printed.
    """
    if not cycle_ids:
        return 0

    placeholders = ",".join(["%s"] * len(cycle_ids))

    return query(
        f"""
        UPDATE cycles
        SET printed = 1
        WHERE id IN ({placeholders})
          AND printed = 0
        """,
        tuple(cycle_ids),
    )


# ======================================================
# PRINT AUDIT TRAIL
# ======================================================

def log_print_event(
    cycle_id: int,
    print_type: str,
    printed_by: Optional[str] = None,
    reason: Optional[str] = None,
) -> int:
    """
    Log AUTO / MANUAL / REPRINT event.
    """
    return query(
        """
        INSERT INTO cycle_print_log
            (cycle_id, print_type, printed_by, reason)
        VALUES (%s, %s, %s, %s)
        """,
        (cycle_id, print_type, printed_by, reason),
    )


def get_print_history(cycle_id: int) -> List[dict]:
    """
    Full print history for audit UI.
    """
    return query(
        """
        SELECT
            print_type,
            printed_at,
            printed_by,
            reason
        FROM cycle_print_log
        WHERE cycle_id = %s
        ORDER BY printed_at ASC
        """,
        (cycle_id,),
    )


# ======================================================
# REPRINT SUPPORT (NO STATE CHANGE)
# ======================================================

def get_cycle_for_reprint(cycle_id: int) -> Optional[dict]:
    """
    Fetch QR data for reprinting by cycle ID.
    """
    rows = query(
        """
        SELECT
            id,
            qr_code
        FROM cycles
        WHERE id = %s
          AND qr_code IS NOT NULL
        """,
        (cycle_id,),
    )

    return rows[0] if rows else None
