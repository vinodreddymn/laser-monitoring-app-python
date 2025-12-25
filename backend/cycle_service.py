# ======================================================
# Cycle Processing Service (Single Source of Truth)
# ======================================================

import logging

from backend.qr_generator import generate_and_save_qr_code
from backend.cycles_dao import log_cycle, mark_printed
from backend.live_print import try_print_live_cycle
from backend.sms_dao import queue_sms_by_model

log = logging.getLogger(__name__)


def handle_detected_cycle(cycle: dict, signals):
    """
    SINGLE authoritative handler for a detected cycle.

    Flow (IMPORTANT ORDER):
    1. Generate QR (PASS only)
    2. Emit UI signal (cycle_detected)
    3. Log cycle to DB
    4. Live auto-print (PASS)
    5. Queue SMS (FAIL)
    """

    # --------------------------------------------------
    # BASIC DATA
    # --------------------------------------------------
    status = cycle.get("pass_fail")
    model_id = cycle.get("model_id")

    qr_text = None
    qr_image_path = None
    qr_code_id = None

    # --------------------------------------------------
    # QR GENERATION (PASS ONLY)
    # --------------------------------------------------
    if status == "PASS":
        try:
            qr = generate_and_save_qr_code(
                model_name=cycle.get("model_name", "UNKNOWN"),
                peak_value=cycle.get("peak_height", 0.0),
                timestamp=cycle.get("timestamp")
            )

            qr_text = qr.get("text")
            qr_image_path = qr.get("absolutePath")
            qr_code_id = qr.get("id")

            cycle["qr_text"] = qr_text
            cycle["qr_code_id"] = qr_code_id
            cycle["qr_image_path"] = qr_image_path

            log.info(
                "QR generated",
                extra={
                    "qr_text": qr_text,
                    "model": cycle.get("model_name"),
                    "peak": cycle.get("peak_height"),
                },
            )

        except Exception:
            log.exception("QR generation failed")

    # --------------------------------------------------
    # EMIT UI SIGNAL (AFTER QR IS READY)
    # --------------------------------------------------
    try:
        signals.cycle_detected.emit(cycle)
    except Exception as e:
        log.error("Failed to emit cycle_detected signal: %s", e)

    # --------------------------------------------------
    # LOG CYCLE TO DATABASE
    # --------------------------------------------------
    try:
        cycle_id = log_cycle(cycle)
        log.info(
            "Cycle logged",
            extra={
                "cycle_id": cycle_id,
                "result": status,
                "peak": cycle.get("peak_height"),
            },
        )
    except Exception:
        log.exception("Failed to log cycle")
        return None

    # --------------------------------------------------
    # LIVE AUTO-PRINT (PASS ONLY)
    # --------------------------------------------------
    if status == "PASS" and qr_text and qr_image_path:
        ok, err = try_print_live_cycle(
            {
                "id": cycle_id,
                "qr_code": qr_text,
                "qr_image_path": qr_image_path,  # REQUIRED
                "model_name": cycle.get("model_name", "UNKNOWN"),
                "pass_fail": status,
            }
        )

        if ok:
            try:
                mark_printed(cycle_id)
                log.info("Label printed for cycle %s", cycle_id)
            except Exception as e:
                log.warning(
                    "Label printed but failed to mark printed: %s", e
                )
        else:
            log.warning("Label NOT printed (live): %s", err)

    elif status == "PASS":
        log.warning(
            "Skipping print: qr_text=%s qr_image_path=%s",
            qr_text,
            qr_image_path,
        )

    # --------------------------------------------------
    # SMS ALERT (FAIL ONLY)
    # --------------------------------------------------
    if status == "FAIL" and model_id:
        try:
            queue_sms_by_model(model_id, cycle)
            log.warning("FAIL SMS queued")
        except Exception as e:
            log.error("Failed to queue FAIL SMS: %s", e)

    return cycle_id
