# ======================================================
# SMS Queue Data Access Layer (PRODUCTION SAFE)
# ======================================================

from datetime import datetime
from typing import List, Dict

from .db import query
from backend.model_watchdog import get_cached_model, register_listener
from .alert_phones_dao import get_all_alert_contacts


# ======================================================
# LOCAL MODEL CACHE (USED FOR SMS FORMATTING)
# ======================================================
_SMS_MODEL_CACHE = {
    "id": None,
    "name": None,
    "lower": None,
    "upper": None,
}


# ======================================================
# INTERNAL HELPERS
# ======================================================
def _format_timestamp(value) -> str:
    """
    Convert ISO / datetime / unknown into MySQL DATETIME string.
    """
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        dt = datetime.now()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ======================================================
# WATCHDOG → CACHE UPDATE
# ======================================================
def _update_local_cache(model: dict):
    """
    Keeps an always-fresh model cache for SMS formatting.
    """
    if not model:
        return

    try:
        _SMS_MODEL_CACHE["id"] = model.get("id")
        _SMS_MODEL_CACHE["name"] = model.get("name")
        _SMS_MODEL_CACHE["lower"] = float(
            model.get("lower_limit", model.get("lower", 0.0))
        )
        _SMS_MODEL_CACHE["upper"] = float(
            model.get("upper_limit", model.get("upper", 0.0))
        )

        print("sms_dao: active model cache updated:", _SMS_MODEL_CACHE)

    except Exception as e:
        print("sms_dao: cache update failed:", e)


# Register watchdog listener
register_listener(_update_local_cache)

# Prime cache on startup
try:
    _update_local_cache(get_cached_model())
except Exception:
    pass


# ======================================================
# MAIN API — QUEUE FAIL SMS
# ======================================================
def queue_sms_by_model(model_id: int, cycle: dict):
    """
    Queue FAIL SMS for all alert contacts linked to a model.

    Stores:
    - name
    - phone
    - message
    - retry metadata
    """

    contacts = get_all_alert_contacts(model_id)
    if not contacts:
        return

    # -------------------------------
    # MODEL NAME
    # -------------------------------
    model_name = (
        cycle.get("model_name")
        or _SMS_MODEL_CACHE.get("name")
        or "Unknown"
    )

    # -------------------------------
    # TIME
    # -------------------------------
    try:
        ts_obj = datetime.fromisoformat(
            str(cycle.get("timestamp")).replace("Z", "+00:00")
        )
        time_str = ts_obj.strftime("%H:%M:%S")
    except Exception:
        time_str = "Unknown"

    # -------------------------------
    # RANGE & PEAK
    # -------------------------------
    lower = _SMS_MODEL_CACHE.get("lower")
    upper = _SMS_MODEL_CACHE.get("upper")
    peak = float(cycle.get("peak_height", 0.0))

    if lower is not None and upper is not None:
        range_text = f"{lower:.2f}–{upper:.2f}"
    else:
        range_text = "N/A"

    # -------------------------------
    # FINAL SMS TEXT (SINGLE SMS)
    # -------------------------------
    message = (
        f"FAIL | {model_name} | "
        f"{peak:.2f}mm (Range: {range_text}) | {time_str}"
    )

    # DB timestamp
    db_ts = _format_timestamp(
        cycle.get("timestamp", datetime.now())
    )

    # -------------------------------
    # INSERT PER CONTACT
    # -------------------------------
    for contact in contacts:
        name = contact.get("name")
        phone = contact.get("phone_number")

        if not phone:
            continue

        query(
            """
            INSERT INTO sms_queue
                (timestamp, name, phone, message, status, retry_count)
            VALUES
                (%s, %s, %s, %s, 'pending', 0)
            """,
            (db_ts, name, phone, message),
        )


# ======================================================
# QUEUE READERS
# ======================================================
def get_pending_sms(limit: int = 10) -> List[Dict]:
    return query(
        """
        SELECT *
        FROM sms_queue
        WHERE status = 'pending'
        ORDER BY id ASC
        LIMIT %s
        """,
        (limit,),
    )


def get_failed_sms_for_retry(
    max_retries: int = 3,
    max_age_seconds: int = 86400,
) -> List[Dict]:
    return query(
        """
        SELECT *
        FROM sms_queue
        WHERE status = 'failed'
          AND retry_count < %s
          AND timestamp > DATE_SUB(NOW(), INTERVAL %s SECOND)
        ORDER BY timestamp ASC
        """,
        (max_retries, max_age_seconds),
    )


# ======================================================
# STATUS UPDATERS
# ======================================================
def mark_sms_sent(sms_id: int):
    query(
        """
        UPDATE sms_queue
        SET status = 'sent',
            retry_count = 0,
            last_error = NULL
        WHERE id = %s
        """,
        (sms_id,),
    )


def increment_sms_retry(sms_id: int, error: str) -> int:
    """
    Increment retry count and mark SMS as failed.
    Returns updated retry count.
    """
    query(
        """
        UPDATE sms_queue
        SET status = 'failed',
            retry_count = retry_count + 1,
            last_error = %s
        WHERE id = %s
        """,
        (str(error)[:255], sms_id),
    )

    row = query(
        "SELECT retry_count FROM sms_queue WHERE id = %s",
        (sms_id,),
        fetch_one=True,
    )

    return int(row["retry_count"]) if row else 0
