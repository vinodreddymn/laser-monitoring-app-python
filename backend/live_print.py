# backend/live_print.py
# ======================================================
# Live Printing Facade
# ======================================================

import logging

from backend.usb_printer_manager import usb_printer

log = logging.getLogger(__name__)


def try_print_live_cycle(cycle_row: dict):
    """
    Unified live print entry.
    Delegates to USBLabelPrinter.
    """
    try:
        result = usb_printer.print_cycle(cycle_row)
        log.info("Live print attempted for cycle %s", cycle_row.get('id', 'unknown'))
        return result
    except Exception as e:
        log.exception("Live print failed for cycle %s", cycle_row.get('id', 'unknown'))
        return False
