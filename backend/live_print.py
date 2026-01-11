# ======================================================
# Live Printing Facade
# ======================================================

import logging
import os

from backend.usb_printer_manager import usb_printer
from backend.qr_generator import generate_qr_for_reprint

log = logging.getLogger(__name__)


def try_print_live_cycle(cycle_row: dict):
    """
    Unified live print entry.

    Rules:
    - If QR image exists → print directly
    - If missing (archived) → regenerate QR
      using ONLY data from cycles / cycles_archive
    """

    try:
        qr_image_path = cycle_row.get("qr_image_path")

        # --------------------------------------------------
        # 🔁 ARCHIVED / MISSING IMAGE → REGENERATE
        # --------------------------------------------------
        if not qr_image_path or not os.path.exists(qr_image_path):
            log.warning(
                "QR image missing for cycle %s → regenerating from cycle data",
                cycle_row.get("id", "unknown")
            )

            # ---- STRICT VALIDATION ----
            required = ["qr_code", "model_name", "peak_height", "timestamp"]
            missing = [k for k in required if not cycle_row.get(k)]
            if missing:
                raise ValueError(
                    f"Cannot regenerate QR, missing fields: {missing}"
                )

            qr = generate_qr_for_reprint(
                qr_text=cycle_row["qr_code"],
                model_name=cycle_row["model_name"],
                model_type=cycle_row.get("model_type"),  # must come from cycle if available
                peak_value=cycle_row["peak_height"],
                timestamp=cycle_row["timestamp"],
            )

            # Avoid mutating caller
            cycle_row = dict(cycle_row)
            cycle_row["qr_image_path"] = qr["absolutePath"]

        # --------------------------------------------------
        # 🖨 PRINT
        # --------------------------------------------------
        result = usb_printer.print_cycle(cycle_row)

        log.info(
            "Live print attempted for cycle %s",
            cycle_row.get("id", "unknown")
        )

        return result

    except Exception as e:
        log.exception(
            "Live print failed for cycle %s",
            cycle_row.get("id", "unknown")
        )
        return False, str(e)
