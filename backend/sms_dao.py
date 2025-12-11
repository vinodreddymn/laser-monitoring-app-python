# backend/sms_dao.py

from .db import query
from datetime import datetime

# Import shared cache + listener from watchdog
from backend.model_watchdog import get_cached_model, register_listener

# ------------------------------------------------------------------
# LOCAL MODEL CACHE (LIGHTWEIGHT & FAST)
# ------------------------------------------------------------------
_SMS_MODEL_CACHE = {
    "id": None,
    "name": None,
    "lower": None,
    "upper": None
}


# ------------------------------------------------------------------
# TIMESTAMP CONVERSION
# ------------------------------------------------------------------
def _format_timestamp(iso_string: str) -> str:
    """Convert ISO timestamp to MySQL DATETIME format safely."""
    try:
        dt = datetime.fromisoformat(iso_string.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ------------------------------------------------------------------
# WATCHDOG LISTENER → Update local SMS model cache
# ------------------------------------------------------------------
def _update_local_cache(model: dict):
    """Maintain local cache for SMS formatting including limits."""
    if not model:
        return
    try:
        _SMS_MODEL_CACHE["id"] = model.get("id")
        _SMS_MODEL_CACHE["name"] = model.get("name")
        _SMS_MODEL_CACHE["lower"] = float(model.get("lower_limit", model.get("lower", 0)))
        _SMS_MODEL_CACHE["upper"] = float(model.get("upper_limit", model.get("upper", 0)))

        print("sms_dao: active model cache updated:", _SMS_MODEL_CACHE)
    except Exception as e:
        print("sms_dao: failed to update cache:", e)


# Register listener for real-time updates
register_listener(_update_local_cache)

# Prime cache on startup
try:
    _update_local_cache(get_cached_model())
except Exception:
    pass


# ------------------------------------------------------------------
# MAIN FUNCTION — QUEUE SMS
# ------------------------------------------------------------------
def queue_sms_by_model(model_id: int, cycle: dict):
    """
    Queue SMS for phone numbers linked to the model when FAIL occurs.
    Uses cached model data (no DB calls).
    """

    from .alert_phones_dao import get_all_phone_numbers

    phones = get_all_phone_numbers(model_id)
    if not phones:
        return

    # Fallback model name priority:
    model_name = (
        cycle.get("model_name")
        or _SMS_MODEL_CACHE.get("name")
        or "Unknown"
    )

    # Format cycle time
    try:
        ts_obj = datetime.fromisoformat(cycle["timestamp"])
        time_str = ts_obj.strftime("%H:%M:%S")
    except Exception:
        time_str = "Unknown"

    # Retrieve allowed range from cache
    lower = _SMS_MODEL_CACHE.get("lower")
    upper = _SMS_MODEL_CACHE.get("upper")
    peak = cycle.get("peak_height", 0)

    if lower is not None and upper is not None:
        range_text = f"{lower:.2f}–{upper:.2f}"
    else:
        range_text = "N/A"

    # ------------------------------------------------------------------
    # Final SMS — MOBILE FRIENDLY (SINGLE LINE)
    # ------------------------------------------------------------------
    msg = (
        f"FAIL | {model_name} | {peak:.2f}mm (Range: {range_text}) | {time_str}"
    )

    # Timestamp for DB insertion
    ts = _format_timestamp(cycle.get("timestamp", datetime.now().isoformat()))

    # Insert SMS entries into queue
    for phone in phones:
        query(
            "INSERT INTO sms_queue (timestamp, phone, message, status) "
            "VALUES (%s, %s, %s, 'pending')",
            (ts, phone, msg)
        )


# ------------------------------------------------------------------
# SMS QUEUE HELPERS
# ------------------------------------------------------------------
def get_pending_sms(limit: int = 10) -> list:
    return query(
        "SELECT * FROM sms_queue WHERE status = 'pending' ORDER BY id ASC LIMIT %s",
        (limit,)
    )


def get_failed_sms_for_retry(max_retries: int = 5, max_age_seconds: int = 86400) -> list:
    return query("""
        SELECT * FROM sms_queue 
        WHERE status = 'failed'
          AND (retry_count IS NULL OR retry_count < %s)
          AND timestamp > DATE_SUB(NOW(), INTERVAL %s SECOND)
        ORDER BY timestamp ASC
    """, (max_retries, max_age_seconds))


def mark_sms_sent(sms_id: int):
    query(
        "UPDATE sms_queue SET status = 'sent', retry_count = 0, last_error = NULL "
        "WHERE id = %s",
        (sms_id,)
    )


def mark_sms_failed(sms_id: int, error_msg: str, retry_count: int = None):
    """Record SMS failure + increment retry count."""
    if retry_count is None:
        query("""
            UPDATE sms_queue 
            SET status = 'failed', last_error = %s,
                retry_count = COALESCE(retry_count, 0) + 1
            WHERE id = %s
        """, (str(error_msg)[:255], sms_id))
    else:
        query("""
            UPDATE sms_queue 
            SET status = 'failed', last_error = %s,
                retry_count = %s
            WHERE id = %s
        """, (str(error_msg)[:255], retry_count, sms_id))
