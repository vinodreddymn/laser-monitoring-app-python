# ======================================================
# MODEM-AWARE SMS ENGINE (PRODUCTION SAFE, PYTHON 3.9)
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
from backend.gsm_modem import send_gsm_message, gsm, modem_signals

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
# INTERNAL STATE
# ======================================================
_sms_queue: Queue = Queue()

_in_flight: Set[int] = set()     # SMS IDs currently being processed
_running = False

_poll_interval = 20              # DB poll interval (seconds)
_max_retries = 3
_send_throttle = 1.5             # delay between SMS sends


# ======================================================
# SMS WORKER LOOP
# ======================================================
def _sms_worker_loop():
    log.info("✅ SMS worker started")

    while _running:
        # Pause if modem disconnected
        if not gsm.is_connected:
            time.sleep(1.0)
            continue

        try:
            # 🔥 MUST MATCH WHAT DB POLLER PUTS IN
            sms_id, name, phone, message = _sms_queue.get(timeout=1)
        except Empty:
            continue

        log.info(
            "📤 Sending SMS → %s (%s) [id=%s]",
            name or "Unknown",
            phone,
            sms_id,
        )

        result = send_gsm_message(phone, message)

        if result.get("success"):
            try:
                mark_sms_sent(sms_id)

                log.info(
                    "✅ SMS sent → %s (%s) [id=%s]",
                    name or "Unknown",
                    phone,
                    sms_id,
                )

                # 🔔 Notify UI (footer)
                sms_signals.sms_sent.emit({
                    "name": name or "Unknown",
                    "phone": phone,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": message,
                })

            except Exception as e:
                log.error("Failed to mark SMS sent (id=%s): %s", sms_id, e)

            finally:
                _in_flight.discard(sms_id)

        else:
            error = result.get("error", "UNKNOWN")
            log.warning("❌ SMS failed (id=%s): %s", sms_id, error)

            try:
                retry_count = increment_sms_retry(sms_id, error)
            except Exception as e:
                log.error("Retry update failed (id=%s): %s", sms_id, e)
                retry_count = _max_retries

            _in_flight.discard(sms_id)

            if retry_count < _max_retries:
                log.info(
                    "🔁 SMS scheduled for retry (id=%s, retry=%s)",
                    sms_id,
                    retry_count,
                )
            else:
                log.error("🛑 SMS permanently failed (id=%s)", sms_id)

        # IMPORTANT: throttle modem
        time.sleep(_send_throttle)


# ======================================================
# DB POLLER LOOP
# ======================================================
def _db_poll_loop():
    log.info("📡 SMS DB poller started")

    while _running:
        if gsm.is_connected:
            try:
                # 1️⃣ Pending SMS
                for row in get_pending_sms(limit=10):
                    sms_id = row["id"]

                    if sms_id in _in_flight:
                        continue

                    _in_flight.add(sms_id)
                    _sms_queue.put((
                        sms_id,
                        row.get("name"),
                        row["phone"],
                        row["message"],
                    ))

                # 2️⃣ Failed SMS eligible for retry
                for row in get_failed_sms_for_retry(max_retries=_max_retries):
                    sms_id = row["id"]

                    if sms_id in _in_flight:
                        continue

                    _in_flight.add(sms_id)
                    _sms_queue.put((
                        sms_id,
                        row.get("name"),
                        row["phone"],
                        row["message"],
                    ))

            except Exception as e:
                log.error("SMS DB poll failed: %s", e)

        time.sleep(_poll_interval)


# ======================================================
# PUBLIC API
# ======================================================
def start_sms_sender(interval_sec: int = 20):
    global _running, _poll_interval

    if _running:
        log.info("SMS sender already running")
        return

    _poll_interval = max(5, int(interval_sec))
    _running = True

    threading.Thread(
        target=_sms_worker_loop,
        daemon=True,
        name="SMSWorker",
    ).start()

    threading.Thread(
        target=_db_poll_loop,
        daemon=True,
        name="SMSDBPoller",
    ).start()

    log.info("🚀 SMS sender started (poll=%ss)", _poll_interval)


def stop_sms_sender():
    global _running
    _running = False
    _in_flight.clear()
    log.info("🛑 SMS sender stopping")
