# ======================================================
# backend/cycles_dao.py
# Pneumatic Laser QC System
#
# Responsibilities:
# - Persist detected cycles
# - Maintain active model cache (via watchdog)
# - Provide recent cycles for dashboards
# - Provide pending QR cycles for manual printing
# - Safely mark cycles as printed
# - Log all print / reprint events (audit trail)
# ======================================================

from datetime import datetime
import logging
from typing import List, Optional

from .db import query
from backend.model_watchdog import get_cached_model, register_listener

log = logging.getLogger(__name__)

# ======================================================
# ACTIVE MODEL CACHE (LOCAL, FAST)
# ======================================================

ACTIVE_MODEL_CACHE = {
    "id": None,
    "name": None,
    "lower_limit": 0.0,
    "upper_limit": 100.0,
}

# ======================================================
# INTERNAL HELPERS
# ======================================================

def _format_timestamp(iso_string: str) -> str:
    """
    Convert ISO timestamp to MySQL DATETIME format safely.
    Falls back to current time if parsing fails.
    """
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        log.warning("cycles_dao: invalid timestamp '%s', using now()", iso_string)
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _update_local_cache(model: dict):
    """
    Update the module-local active model cache when watchdog notifies.
    Avoids DB hits on the hot cycle-detection path.
    """
    if not model:
        return

    try:
        ACTIVE_MODEL_CACHE["id"] = model.get("id")
        ACTIVE_MODEL_CACHE["name"] = model.get("name")
        ACTIVE_MODEL_CACHE["lower_limit"] = float(
            model.get("lower_limit", model.get("lower", 0.0))
        )
        ACTIVE_MODEL_CACHE["upper_limit"] = float(
            model.get("upper_limit", model.get("upper", 100.0))
        )

        log.info("cycles_dao: active model cache updated → %s", ACTIVE_MODEL_CACHE)

    except Exception:
        log.exception("cycles_dao: failed to update active model cache")


# ======================================================
# WATCHDOG REGISTRATION
# ======================================================

register_listener(_update_local_cache)

try:
    _update_local_cache(get_cached_model())
except Exception:
    pass

# ======================================================
# CYCLE PERSISTENCE
# ======================================================

def log_cycle(cycle: dict) -> int:
    """
    Insert a detected cycle into the database.

    Uses the local active model cache for model_id and model_name
    to avoid database access on every cycle.
    """
    formatted_ts = _format_timestamp(
        cycle.get("timestamp", datetime.now().isoformat())
    )

    model_id = ACTIVE_MODEL_CACHE.get("id", cycle.get("model_id"))
    model_name = (
        ACTIVE_MODEL_CACHE.get("name")
        or cycle.get("model_name")
        or "Unknown"
    )

    return query(
        """
        INSERT INTO cycles
            (timestamp, model_id, model_name, peak_height, pass_fail, qr_code)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            formatted_ts,
            model_id,
            model_name,
            cycle.get("peak_height"),
            cycle.get("pass_fail"),
            cycle.get("qr_text"),
        ),
    )


def get_cycles(limit: int = 50) -> list:
    """
    Return recent cycles for dashboards / history views.
    """
    return query(
        "SELECT * FROM cycles ORDER BY id DESC LIMIT %s",
        (limit,),
    )


# ======================================================
# PRINT QUEUE (FIRST-TIME PRINT)
# ======================================================

def get_pending_qr_cycles(limit: int = 100) -> list:
    """
    Return cycles where QR is generated but not printed yet,
    joined with qr_codes to fetch image path.
    """
    return query(
        """
        SELECT
            c.id,
            c.timestamp,
            c.model_name,
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



def mark_printed(cycle_id: int) -> int:
    """
    Mark a cycle as printed (first successful print).
    Idempotent and safe against double-clicks.
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
    Mark multiple cycles as printed in one operation.
    Useful for 'Print All Pending' workflows.
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
# PRINT AUDIT LOG (AUTO / MANUAL / REPRINT)
# ======================================================

def log_print_event(
    cycle_id: int,
    print_type: str,
    printed_by: Optional[str] = None,
    reason: Optional[str] = None,
) -> int:
    """
    Log a print event into cycle_print_log.
    print_type: AUTO | MANUAL | REPRINT
    """
    return query(
        """
        INSERT INTO cycle_print_log
            (cycle_id, print_type, printed_by, reason)
        VALUES (%s, %s, %s, %s)
        """,
        (cycle_id, print_type, printed_by, reason),
    )


def get_print_history(cycle_id: int) -> list:
    """
    Return complete print / reprint history for a cycle.
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
# REPRINT SUPPORT (DOES NOT CHANGE printed FLAG)
# ======================================================

def get_cycle_for_reprint(cycle_id: int) -> Optional[dict]:
    """
    Fetch QR data for reprinting an already printed cycle.
    """
    rows = query(
        """
        SELECT id, qr_code
        FROM cycles
        WHERE id = %s
          AND qr_code IS NOT NULL
        """,
        (cycle_id,),
    )
    return rows[0] if rows else None
