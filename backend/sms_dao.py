# ======================================================
# backend/sms_dao.py
# SMS Queue Data Access Layer (PRODUCTION SAFE)
# ======================================================

from datetime import datetime
from typing import List, Dict
import logging

from .db import query
from backend.model_watchdog import get_cached_model, register_listener
from .alert_phones_dao import get_all_alert_contacts

log = logging.getLogger(__name__)

# ======================================================
# LOCAL MODEL CACHE (FOR SMS CONTENT)
# ======================================================
_SMS_MODEL_CACHE = {
    "id": None,
    "name": None,
    "type": None,
    "lower": None,
    "upper": None,
}

# ======================================================
# INTERNAL TIME HELPERS
# ======================================================
def _format_db_timestamp(value) -> str:
    """
    Normalize timestamp to MySQL DATETIME (YYYY-MM-DD HH:MM:SS)
    """
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
    except Exception:
        dt = datetime.now()

    return dt.strftime("%Y-%m-%d %H:%M:%S")


def _format_date_only(value) -> str:
    """
    DD-MM-YYYY (SMS friendly)
    """
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return "Unknown"


def _format_time_only(value) -> str:
    """
    HH:MM:SS (SMS friendly)
    """
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromisoformat(
                str(value).replace("Z", "+00:00")
            )
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "Unknown"


# ======================================================
# MODEL WATCHDOG → CACHE
# ======================================================
def _update_model_cache(model: dict):
    """
    Keep latest active model details for SMS formatting.
    """
    if not model:
        return

    try:
        _SMS_MODEL_CACHE["id"] = model.get("id")
        _SMS_MODEL_CACHE["name"] = model.get("name")
        _SMS_MODEL_CACHE["type"] = model.get("model_type", "NA")

        _SMS_MODEL_CACHE["lower"] = float(
            model.get("lower_limit", model.get("lower", 0.0))
        )
        _SMS_MODEL_CACHE["upper"] = float(
            model.get("upper_limit", model.get("upper", 0.0))
        )

        log.info("SMS model cache updated: %s", _SMS_MODEL_CACHE)

    except Exception:
        log.exception("SMS model cache update failed")


# Register watchdog listener
register_listener(_update_model_cache)

# Prime cache on startup
try:
    _update_model_cache(get_cached_model())
except Exception:
    pass


# ======================================================
# PUBLIC API — QUEUE SMS
# ======================================================
def queue_sms_by_model(model_id: int, cycle: dict):
    """
    Queue operator-safe SMS for all alert contacts
    when an abnormal cycle is detected.

    NOTE:
    - SMS is best-effort notification
    - Delivery depends on operator & DND
    """

    contacts = get_all_alert_contacts(model_id)
    if not contacts:
        return

    # -------------------------------
    # MODEL DETAILS
    # -------------------------------
    model_name = (
        cycle.get("model_name")
        or _SMS_MODEL_CACHE.get("name")
        or "LINE"
    )

    model_type = _SMS_MODEL_CACHE.get("type", "NA")

    # Remove spaces from model name for SMS safety
    model_name = model_name.replace(" ", "")

    # -------------------------------
    # MEASUREMENT VALUES
    # -------------------------------
    peak = float(cycle.get("peak_height", 0.0))

    lower = _SMS_MODEL_CACHE.get("lower")
    upper = _SMS_MODEL_CACHE.get("upper")

    if lower is not None and upper is not None:
        range_text = f"{lower:.2f} - {upper:.2f} mm"
    else:
        range_text = "NA"

    # -------------------------------
    # DATE & TIME
    # -------------------------------
    date_str = _format_date_only(
        cycle.get("timestamp", datetime.now())
    )

    time_str = _format_time_only(
        cycle.get("timestamp", datetime.now())
    )

    db_timestamp = _format_db_timestamp(
        cycle.get("timestamp", datetime.now())
    )

    # -------------------------------
    # OPERATOR-SAFE SINGLE-LINE SMS
    # -------------------------------
    message = (
        f"NTF QC Fail Alert: "
        f"{model_name} ({model_type}) ({range_text}) - "
        f"Weld depth {peak:.2f} mm "
        f"on {date_str} at {time_str}. "
        f"Info by ASHTECH"
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
            (db_timestamp, name, phone, message),
        )

        log.info(
            "SMS queued → %s (%s)",
            name or "User",
            phone,
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
    log.info("SMS %s marked as sent", sms_id)


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
        """
        SELECT retry_count
        FROM sms_queue
        WHERE id = %s
        """,
        (sms_id,),
        fetch_one=True,
    )

    retry_count = int(row["retry_count"]) if row else 0
    log.warning("SMS %s retry incremented to %s: %s", sms_id, retry_count, error)
    return retry_count
