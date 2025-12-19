# backend/live_print.py
# ======================================================
# Live Printing Facade
# ======================================================

from backend.usb_printer_manager import usb_printer


def try_print_live_cycle(cycle_row: dict):
    """
    Unified live print entry.
    Delegates to USBLabelPrinter.
    """
    return usb_printer.print_cycle(cycle_row)
