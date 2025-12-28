# backend/cycles_dao.py

import os
from datetime import datetime
from .db import query

# Use the shared model cache (very fast)
from backend.model_watchdog import get_cached_model, register_listener
import logging

log = logging.getLogger(__name__)

ACTIVE_MODEL_CACHE = {
    "id": None,
    "name": None,
    "lower_limit": 0.0,
    "upper_limit": 100.0
}


def _format_timestamp(iso_string: str) -> str:
    """Convert ISO timestamp to MySQL DATETIME format safely."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _update_local_cache(model: dict):
    """Update the module-local active model cache when watchdog notifies."""
    if not model:
        return
    try:
        ACTIVE_MODEL_CACHE["id"] = model.get("id")
        ACTIVE_MODEL_CACHE["name"] = model.get("name")
        # accept both lower_limit or lower
        ACTIVE_MODEL_CACHE["lower_limit"] = float(model.get("lower_limit", model.get("lower", 0)))
        ACTIVE_MODEL_CACHE["upper_limit"] = float(model.get("upper_limit", model.get("upper", 100)))
        log.info("cycles_dao: active model cache updated: %s", ACTIVE_MODEL_CACHE)
    except Exception:
        log.exception("cycles_dao: failed to update cache")


# Register cache updater with watchdog
register_listener(_update_local_cache)
# Initialize cache from current cached model (if any)
try:
    _update_local_cache(get_cached_model())
except Exception:
    pass


def log_cycle(cycle: dict) -> int:
    """
    Insert cycle to DB. Uses the local cached active model for model_id/name,
    which avoids hitting the DB for every cycle.
    """
    formatted_ts = _format_timestamp(cycle.get("timestamp", datetime.now().isoformat()))

    model_id = ACTIVE_MODEL_CACHE.get("id", cycle.get("model_id"))
    model_name = ACTIVE_MODEL_CACHE.get("name") or cycle.get("model_name") or "Unknown"

    return query("""
        INSERT INTO cycles 
        (timestamp, model_id, model_name, peak_height, pass_fail, qr_code) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        formatted_ts,
        model_id,
        model_name,
        cycle.get("peak_height"),
        cycle.get("pass_fail"),
        cycle.get("qr_text")
    ))


def get_cycles(limit: int = 50) -> list:
    """Returns recent cycles."""
    return query("SELECT * FROM cycles ORDER BY id DESC LIMIT %s", (limit,))


def mark_printed(cycle_id: int) -> int:
    """Mark a cycle as printed."""
    return query("UPDATE cycles SET printed = 1 WHERE id = %s", (cycle_id,))
