# backend/sms_sender.py — NON-BLOCKING PRODUCTION ENGINE (UI SIGNAL ENABLED)

import time
import threading
import logging
from queue import Queue
from datetime import datetime

from PySide6.QtCore import QObject, Signal

from backend.sms_dao import get_pending_sms, mark_sms_sent
from backend.gsm_modem import send_gsm_message

logger = logging.getLogger(__name__)


# ======================================================
# ✅ Qt Signals to update GUI (MainWindow)
# ======================================================
class SMSSignals(QObject):
    sms_engine = Signal(bool)      # True = running, False = stopped
    sms_sent = Signal(dict)        # {phone, time, message}

sms_signals = SMSSignals()


# ======================================================
# Internal Worker State
# ======================================================
_sms_queue = Queue()
_worker_running = False
_worker_thread = None


# ======================================================
# SMS WORKER THREAD  (SENDS SMS OUT)
# ======================================================
def _sms_worker():
    global _worker_running

    print("✅ SMS Worker Thread Started")
    sms_signals.sms_engine.emit(True)   # UI update → running

    while _worker_running:
        try:
            task = _sms_queue.get(timeout=1)
        except:
            continue

        if not task:
            continue

        sms_id, phone, message = task

        try:
            print(f"📤 Sending SMS → {phone}")
            result = send_gsm_message(phone, message)

            if result.get("success"):
                print(f"✅ SMS sent to {phone}")
                mark_sms_sent(sms_id)

                # ===============================
                # Notify UI of last SMS sent
                # ===============================
                sms_signals.sms_sent.emit({
                    "phone": phone,
                    "time": datetime.now().strftime("%H:%M:%S"),
                    "message": message
                })

            else:
                error = result.get("error", "Unknown GSM error")
                print(f"❌ SMS failed to {phone}: {error}")

        except Exception as e:
            logger.error(f"SMS worker error: {e}")

        time.sleep(1.2)  # rate limit


# ======================================================
# POLL DB FOR PENDING SMS
# ======================================================
def _poll_db_for_pending_sms():
    try:
        pending = get_pending_sms(limit=10)

        if pending:
            print(f"[SMS Sender] Queuing {len(pending)} message(s)")

        for row in pending:
            sms_id = row["id"]
            phone = row["phone"]
            message = row["message"]

            _sms_queue.put((sms_id, phone, message))

    except Exception as e:
        logger.error(f"SMS poll error: {e}")


# ======================================================
# START SMS ENGINE
# ======================================================
def start_sms_sender(interval_sec=20):
    """
    Starts DB poller + worker thread (NON-BLOCKING)
    """
    global _worker_running, _worker_thread

    if _worker_running:
        return

    _worker_running = True

    # Start worker thread
    _worker_thread = threading.Thread(target=_sms_worker, daemon=True)
    _worker_thread.start()

    print(f"✅ SMS Sender Engine → STARTED (checks every {interval_sec}s)")

    # Poll loop
    def _poll_loop():
        if not _worker_running:
            return

        _poll_db_for_pending_sms()
        threading.Timer(interval_sec, _poll_loop).start()

    _poll_loop()

    # UI: Engine started
    sms_signals.sms_engine.emit(True)


# ======================================================
# STOP SMS ENGINE
# ======================================================
def stop_sms_sender():
    global _worker_running

    print("🛑 Stopping SMS Sender Engine...")
    _worker_running = False

    # UI: Engine stopped
    sms_signals.sms_engine.emit(False)
