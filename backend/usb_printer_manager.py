# ======================================================
# backend/usb_printer_manager.py
# USB / Virtual Label Printer Manager (SILENT PRINT)
# ======================================================

import time
import logging
from threading import Thread
from pathlib import Path
from typing import Optional

import win32print
import win32ui
from PIL import Image, ImageWin

from PySide6.QtCore import QObject, Signal

from config.app_config import (
    PRINTER_CHECK_INTERVAL,
    EXCLUDED_PRINTERS,
    DEFAULT_PRINTER_NAME
)

log = logging.getLogger(__name__)

# ======================================================
# SIGNALS
# ======================================================

class PrinterSignals(QObject):
    """
    Emits:
        printer_status(bool connected, str printer_name)
    """
    printer_status = Signal(bool, str)


printer_signals = PrinterSignals()

# ======================================================
# PRINTER MANAGER
# ======================================================

class USBLabelPrinter:
    """
    USB / Virtual Printer Manager

    - Auto-detects printer
    - Emits status changes
    - Prints images silently using Win32 GDI
    """

    def __init__(self):
        self.printer_name: Optional[str] = None
        self.is_connected: bool = False
        self.running = True

        Thread(target=self._monitor_loop, daemon=True).start()
        self._check_once()

    # --------------------------------------------------
    # PUBLIC API
    # --------------------------------------------------
    def emit_current_status(self):
        """Re-emit last known printer status (used by UI on startup)"""
        printer_signals.printer_status.emit(
            self.is_connected,
            self.printer_name if self.is_connected else ""
        )

    # --------------------------------------------------
    def print_cycle(self, cycle_data: dict):
        """
        Print QR label image for a completed cycle
        """
        if not self.is_connected or not self.printer_name:
            return False, "Printer not connected"

        qr_id = cycle_data.get("qr_code_id") or cycle_data.get("qr_id")
        if not qr_id:
            return False, "QR ID missing in cycle data"

        qr_path = Path(__file__).parent.parent / "qr_images" / f"{qr_id}.png"
        if not qr_path.exists():
            return False, f"QR image not found: {qr_path}"

        try:
            self._print_image(str(qr_path))
            log.info(f"🖨 Printed QR label: {qr_id}")
            return True, None
        except Exception as e:
            log.exception("Print failed")
            return False, str(e)

    # --------------------------------------------------
    # SILENT PRINT (NO DIALOG)
    # --------------------------------------------------
    def _print_image(self, image_path: str):
        """
        Silent image printing using Win32 GDI
        (NO print dialog, NO file association)
        """
        hPrinter = win32print.OpenPrinter(self.printer_name)

        try:
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(self.printer_name)

            hdc.StartDoc(image_path)
            hdc.StartPage()

            img = Image.open(image_path).convert("RGB")

            printable_width  = hdc.GetDeviceCaps(8)   # HORZRES
            printable_height = hdc.GetDeviceCaps(10)  # VERTRES

            img_w, img_h = img.size
            scale = min(
                printable_width / img_w,
                printable_height / img_h
            )

            draw_w = int(img_w * scale)
            draw_h = int(img_h * scale)

            x = int((printable_width  - draw_w) / 2)
            y = int((printable_height - draw_h) / 2)

            dib = ImageWin.Dib(img)
            dib.draw(
                hdc.GetHandleOutput(),
                (x, y, x + draw_w, y + draw_h)
            )

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()

        finally:
            win32print.ClosePrinter(hPrinter)

    # --------------------------------------------------
    # MONITORING
    # --------------------------------------------------
    def _emit(self, connected: bool, name: str = ""):
        if self.is_connected == connected:
            return

        self.is_connected = connected
        self.printer_name = name if connected else None

        printer_signals.printer_status.emit(
            connected,
            name if connected else ""
        )

    # --------------------------------------------------
    def _check_once(self):
        try:
            name = self._find_printer()
            if not name:
                raise RuntimeError
            self._emit(True, name)
        except Exception:
            self._emit(False, "")

    # --------------------------------------------------
    def _monitor_loop(self):
        log.info("🖨 Printer monitor started")
        while self.running:
            try:
                name = self._find_printer()
                if not name:
                    raise RuntimeError
                self._emit(True, name)
            except Exception:
                self._emit(False, "")
            time.sleep(PRINTER_CHECK_INTERVAL)

    # --------------------------------------------------
    def _find_printer(self) -> Optional[str]:
        """
        Find a ready printer:
        1) Prefer configured printer
        2) Fallback to any ready printer
        """
        try:
            printers = win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL |
                win32print.PRINTER_ENUM_CONNECTIONS
            )

            # 1️⃣ Configured printer
            if DEFAULT_PRINTER_NAME:
                for _, _, name, _ in printers:
                    if name == DEFAULT_PRINTER_NAME and self._is_ready(name):
                        return name

            # 2️⃣ Any suitable printer
            for _, _, name, _ in printers:
                lname = name.lower()
                if any(x in lname for x in EXCLUDED_PRINTERS):
                    continue
                if self._is_ready(name):
                    return name

        except Exception as e:
            log.warning(f"Printer enumeration failed: {e}")

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


# ======================================================
# SINGLETON INSTANCE
# ======================================================

usb_printer = USBLabelPrinter()
