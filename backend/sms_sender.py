# ======================================================
# backend/sms_sender.py
# Reliable SMS Engine – A7670C SAFE
# ======================================================

import time
import threading
import logging
from queue import Queue, Empty
from datetime import datetime
from typing import Set

from PySide6.QtCore import QObject, Signal

from backend.sms_dao import (
    get_pending_sms,
    get_failed_sms_for_retry,
    mark_sms_sent,
    increment_sms_retry,
)
from backend.gsm_modem import gsm, send_gsm_message, modem_signals
from config.app_config import SMS_POLL_INTERVAL

log = logging.getLogger(__name__)

# ======================================================
# UI SIGNALS
# ======================================================
class SMSSignals(QObject):
    modem_status = Signal(bool)
    sms_sent = Signal(dict)

sms_signals = SMSSignals()
modem_signals.modem_connected.connect(sms_signals.modem_status.emit)

# ======================================================
_sms_queue = Queue()
_in_flight: Set[int] = set()
_running = False

_max_retries = 3
_send_delay = 15  # seconds (A7670C stable gap)


# ======================================================
def _sms_worker():
    log.info("📨 SMS worker started")

    while _running:
        if not gsm.is_connected:
            time.sleep(1)
            continue

        try:
            sms_id, name, phone, message = _sms_queue.get(timeout=1)
        except Empty:
            continue

        log.info("📤 Sending SMS → %s (%s)", name or "User", phone)
        log.warning("SMS TEXT >>> %r", message)

        result = send_gsm_message(phone, message)

        if result["success"]:
            mark_sms_sent(sms_id)

            if result["error"] == "SENT_NO_CONFIRM":
                log.warning(
                    "SMS sent without modem confirmation (id=%s)",
                    sms_id,
                )

            sms_signals.sms_sent.emit({
                "name": name or "User",
                "phone": phone,
                "time": datetime.now().strftime("%H:%M:%S"),
                "message": message,
            })

            log.info("✅ SMS sent (id=%s)", sms_id)

        else:
            err = result["error"]
            retry = increment_sms_retry(sms_id, err)
            log.warning("❌ SMS failed (id=%s): %s", sms_id, err)

            if retry >= _max_retries:
                log.error("🛑 SMS permanently failed (id=%s)", sms_id)

        _in_flight.discard(sms_id)
        time.sleep(_send_delay)


# ======================================================
def _db_poller():
    log.info("📡 SMS DB poller started")

    while _running:
        if gsm.is_connected:
            for row in get_pending_sms(limit=10):
                if row["id"] not in _in_flight:
                    _in_flight.add(row["id"])
                    _sms_queue.put((
                        row["id"],
                        row.get("name"),
                        row["phone"],
                        row["message"],
                    ))

            for row in get_failed_sms_for_retry(_max_retries):
                if row["id"] not in _in_flight:
                    _in_flight.add(row["id"])
                    _sms_queue.put((
                        row["id"],
                        row.get("name"),
                        row["phone"],
                        row["message"],
                    ))

        time.sleep(SMS_POLL_INTERVAL)


# ======================================================
# PUBLIC API
# ======================================================
def start_sms_sender():
    global _running

    if _running:
        return

    _running = True

    threading.Thread(target=_sms_worker, daemon=True).start()
    threading.Thread(target=_db_poller, daemon=True).start()

    log.info("🚀 SMS sender started")


def stop_sms_sender():
    global _running
    _running = False
    _in_flight.clear()
