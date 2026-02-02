# ======================================================
# Cycle Processing Service (Single Source of Truth)
# Pneumatic Laser QC System
#
# RESPONSIBILITIES
# ------------------------------------------------------
# 1. Normalize detected cycle data
# 2. Generate QR code (PASS only)
# 3. Emit UI update (Qt thread-safe)
# 4. Persist cycle to database
# 5. Auto-print label (PASS only)
# 6. Queue SMS alert (FAIL only)
#
# IMPORTANT DATA RULE
# ------------------------------------------------------
# DB column `peak_height` STORES **WELD DEPTH**
# (not the raw physical laser peak)
# ======================================================

import logging
from PySide6.QtCore import QTimer

from backend.qr_generator import generate_new_qr
from backend.cycles_dao import (
    log_cycle,
    mark_printed,
    log_print_event,
)
from backend.live_print import try_print_live_cycle
from backend.sms_dao import queue_sms_by_model

log = logging.getLogger(__name__)


def handle_detected_cycle(cycle: dict, signals):
    """
    SINGLE authoritative handler for a detected welding cycle.

    EXECUTION ORDER (DO NOT CHANGE):
    1. Normalize cycle data
    2. Generate QR (PASS only)
    3. Emit UI signal (Qt-safe)
    4. Log cycle to DB
    5. Auto-print label (PASS only)
    6. Queue SMS alert (FAIL only)
    """

    # ==================================================
    # BASIC DATA EXTRACTION
    # ==================================================
    status = cycle.get("pass_fail")
    model_id = cycle.get("model_id")

    weld_depth = float(cycle.get("weld_depth", 0.0))
    touch_point = float(cycle.get("touch_point", 0.0))

    # ==================================================
    # 🔑 NORMALIZE FOR STORAGE & DOWNSTREAM USE
    # ==================================================
    # DB field `peak_height` intentionally stores WELD DEPTH
    cycle["peak_height"] = weld_depth

    qr_text = None
    qr_image_path = None

    # ==================================================
    # QR GENERATION (PASS ONLY)
    # ==================================================
    if status == "PASS":
        try:
            qr = generate_new_qr(
                model_name=cycle.get("model_name", "UNKNOWN"),
                peak_value=weld_depth,          # weld depth on QR
                timestamp=cycle.get("timestamp"),
            )

            qr_text = qr["qr_text"]
            qr_image_path = qr["absolutePath"]

            cycle.update({
                "qr_text": qr_text,
                "qr_code": qr_text,
                "qr_image_path": qr_image_path,
                "model_type": qr["model_type"],
            })

            log.info(
                "QR generated | %s | weld_depth=%.2f mm",
                qr_text,
                weld_depth,
            )

        except Exception:
            log.exception("QR generation failed")

    # ==================================================
    # UI UPDATE (Qt THREAD-SAFE)
    # ==================================================
    QTimer.singleShot(
        0,
        lambda c=dict(cycle): signals.cycle_detected.emit(c)
    )

    # ==================================================
    # LOG CYCLE TO DATABASE
    # ==================================================
    try:
        cycle_id = log_cycle(cycle)
        log.info(
            "Cycle logged | id=%s | result=%s | weld_depth=%.2f",
            cycle_id,
            status,
            weld_depth,
        )
    except Exception:
        log.exception("Failed to log cycle")
        return None

    # ==================================================
    # AUTO-PRINT LABEL (PASS ONLY)
    # ==================================================
    if status == "PASS" and qr_text and qr_image_path:
        ok, err = try_print_live_cycle({
            "id": cycle_id,
            "timestamp": cycle.get("timestamp"),
            "qr_code": qr_text,
            "qr_code_id": qr_text,
            "qr_image_path": qr_image_path,
            "model_name": cycle.get("model_name", "UNKNOWN"),
            "model_type": cycle.get("model_type", "RHD"),

            # Quality data
            "peak_height": weld_depth,   # weld depth by definition
            "touch_point": touch_point,
            "pass_fail": status,
        })

        if ok:
            try:
                mark_printed(cycle_id)
                log_print_event(
                    cycle_id=cycle_id,
                    print_type="AUTO",
                    printed_by="SYSTEM",
                    reason=None,
                )
                log.info("Label printed (AUTO) | cycle=%s", cycle_id)
            except Exception:
                log.exception("Print succeeded but DB update failed")
        else:
            log.warning("AUTO print failed: %s", err)

    # ==================================================
    # SMS ALERT (FAIL ONLY)
    # ==================================================
    if status == "FAIL" and model_id:
        try:
            queue_sms_by_model(model_id, cycle)
            log.warning(
                "FAIL SMS queued | model=%s | weld_depth=%.2f",
                model_id,
                weld_depth,
            )
        except Exception:
            log.exception("Failed to queue FAIL SMS")

    return cycle_id
