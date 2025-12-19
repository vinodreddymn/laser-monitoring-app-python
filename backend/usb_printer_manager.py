# backend/usb_printer_manager.py
# ======================================================
# USB / Virtual Label Printer Manager
# ======================================================

import time
import logging
from threading import Thread
from typing import Optional
from pathlib import Path
from datetime import datetime

import win32print
from PySide6.QtCore import QObject, Signal

from backend.label_builder import build_zpl_label
from backend.pdf_label_renderer import render_label_pdf

log = logging.getLogger(__name__)

# ======================================================
# CONFIGURATION
# ======================================================

PRINTER_NAME = "PDFCreator"   # Change to Zebra later
CHECK_INTERVAL = 5.0
EXCLUDED_PRINTERS = ("onenote",)

PDF_OUTPUT_DIR = Path("prints")

# ======================================================
# SIGNALS
# ======================================================

class PrinterSignals(QObject):
    printer_connected = Signal(bool)


printer_signals = PrinterSignals()

# ======================================================
# PRINTER MANAGER
# ======================================================

class USBLabelPrinter:
    def __init__(self):
        self.printer_name = PRINTER_NAME
        self.is_connected = False
        self.running = True

        PDF_OUTPUT_DIR.mkdir(exist_ok=True)

        Thread(
            target=self._monitor,
            daemon=True,
            name="PrinterMonitor"
        ).start()

    # --------------------------------------------------
    def _set_connected(self, state: bool):
        if self.is_connected == state:
            return

        self.is_connected = state
        printer_signals.printer_connected.emit(state)

        if state:
            log.info("🟢 PRINTER CONNECTED → %s", self.printer_name)
        else:
            log.warning("🔴 PRINTER DISCONNECTED")

    # --------------------------------------------------
    def _find_printer(self) -> Optional[str]:
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL |
            win32print.PRINTER_ENUM_CONNECTIONS
        )

        for _, _, name, _ in printers:
            lname = name.lower()
            if any(x in lname for x in EXCLUDED_PRINTERS):
                continue
            if name == self.printer_name:
                return name
        return None

    # --------------------------------------------------
    def _is_ready(self, name: str) -> bool:
        try:
            h = win32print.OpenPrinter(name)
            info = win32print.GetPrinter(h, 2)
            win32print.ClosePrinter(h)
            return info.get("Status", 1) == 0
        except Exception:
            return False

    # --------------------------------------------------
    def _monitor(self):
        log.info("Printer monitor started")

        while self.running:
            try:
                name = self._find_printer()
                if not name or not self._is_ready(name):
                    raise RuntimeError
                self.printer_name = name
                self._set_connected(True)
            except Exception:
                self._set_connected(False)

            time.sleep(CHECK_INTERVAL)

    # --------------------------------------------------
    def print_cycle(self, cycle_row: dict):
        """
        Unified entry point:
        - PDFCreator → PDF
        - Zebra → RAW ZPL
        """
        if not self.is_connected:
            return False, "PRINTER_OFFLINE"

        if self.printer_name.lower() == "pdfcreator":
            return self._print_pdf(cycle_row)
        else:
            return self._print_zpl(cycle_row)

    # --------------------------------------------------
    def _print_pdf(self, cycle_row: dict):
        fname = (
            f"{cycle_row['qr_code']}_"
            f"{datetime.now():%Y%m%d_%H%M%S}.pdf"
        )

        output = PDF_OUTPUT_DIR / fname

        render_label_pdf(
            output_path=str(output),
            label_image_path=cycle_row["qr_image_path"],  # ✅ absolute PNG path
        )

        log.info("📄 PDF LABEL SAVED → %s", output)
        return True, None


    # --------------------------------------------------
    def _print_zpl(self, cycle_row: dict):
        zpl = build_zpl_label(
            qr_text=cycle_row["qr_code"],
            model_name=cycle_row["model_name"],
            result=cycle_row["pass_fail"]
        )

        try:
            h = win32print.OpenPrinter(self.printer_name)
            win32print.StartDocPrinter(h, 1, ("Label", None, "RAW"))
            win32print.StartPagePrinter(h)
            win32print.WritePrinter(h, zpl.encode("utf-8"))
            win32print.EndPagePrinter(h)
            win32print.EndDocPrinter(h)
            win32print.ClosePrinter(h)

            log.info("🏷 LABEL SENT TO PRINTER")
            return True, None

        except Exception as e:
            log.error("Print failed: %s", e)
            return False, str(e)

    # --------------------------------------------------
    def stop(self):
        self.running = False


# ======================================================
# SINGLETON
# ======================================================

usb_printer = USBLabelPrinter()
