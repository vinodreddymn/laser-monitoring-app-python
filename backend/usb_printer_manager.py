# ======================================================
# backend/usb_printer_manager.py
# USB Label Printer Manager – DPI-AWARE IMAGE PRINT
# ======================================================

import time
import logging
from threading import Thread
from pathlib import Path
from typing import Optional

import win32print
import win32ui
import win32con
from PIL import Image, ImageWin

from PySide6.QtCore import QObject, Signal

from config.app_config import (
    PRINTER_CHECK_INTERVAL,
    EXCLUDED_PRINTERS,
    DEFAULT_PRINTER_NAME
)

log = logging.getLogger(__name__)

# ======================================================
# LABEL CONFIG (PHYSICAL SIZE)
# ======================================================

LABEL_WIDTH_IN = 2.28
LABEL_HEIGHT_IN = 1.46

BACKGROUND_COLOR = "white"   # label background

# ======================================================
# SIGNALS
# ======================================================

class PrinterSignals(QObject):
    printer_status = Signal(bool, str)

printer_signals = PrinterSignals()

# ======================================================
# PRINTER MANAGER
# ======================================================

class USBLabelPrinter:
    """
    DPI-aware USB label printer (Windows GDI)

    ✔ Exact physical label size
    ✔ No driver scaling
    ✔ QR always centered
    ✔ Works across printers
    """

    def __init__(self):
        self.printer_name: Optional[str] = None
        self.is_connected = False
        self.running = True

        Thread(target=self._monitor_loop, daemon=True).start()
        self._check_once()

    # --------------------------------------------------
    # STATUS
    # --------------------------------------------------

    def _emit(self, connected: bool, name: str = ""):
        if self.is_connected == connected and self.printer_name == name:
            return
        self.is_connected = connected
        self.printer_name = name if connected else None
        printer_signals.printer_status.emit(connected, name)

    def _check_once(self):
        try:
            name = self._find_printer()
            self._emit(bool(name), name or "")
        except Exception:
            self._emit(False, "")

    def _monitor_loop(self):
        while self.running:
            try:
                name = self._find_printer()
                self._emit(bool(name), name or "")
            except Exception:
                self._emit(False, "")
            time.sleep(PRINTER_CHECK_INTERVAL)

    # --------------------------------------------------
    # PUBLIC PRINT API
    # --------------------------------------------------

    def print_cycle(self, cycle_data: dict):
        if not self.is_connected or not self.printer_name:
            return False, "Printer not connected"

        qr_path = cycle_data.get("qr_image_path")
        if not qr_path:
            return False, "QR image path missing"

        qr_path = Path(qr_path)
        if not qr_path.exists():
            return False, f"QR image not found: {qr_path}"

        try:
            self._print_image(qr_path)
            log.info("🖨 Label printed: %s", qr_path.name)
            return True, None
        except Exception as e:
            log.exception("Print failed")
            return False, str(e)

    # --------------------------------------------------
    # CORE IMAGE PRINT (DPI SAFE)
    # --------------------------------------------------

    def _print_image(self, image_path: Path):

        img = Image.open(image_path).convert("RGB")

        hPrinter = win32print.OpenPrinter(self.printer_name)
        try:
            hdc = win32ui.CreateDC()
            hdc.CreatePrinterDC(self.printer_name)
            hdc.SetMapMode(win32con.MM_TEXT)

            # --------------------------------------------------
            # 🔑 REAL PRINTER DPI (DO NOT ASSUME 300)
            # --------------------------------------------------
            dpi_x = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
            dpi_y = hdc.GetDeviceCaps(win32con.LOGPIXELSY)

            log.info("Printer DPI detected: %dx%d", dpi_x, dpi_y)

            # --------------------------------------------------
            # LABEL SIZE IN PRINTER PIXELS
            # --------------------------------------------------
            label_w_px = int(LABEL_WIDTH_IN * dpi_x)
            label_h_px = int(LABEL_HEIGHT_IN * dpi_y)

            # --------------------------------------------------
            # SCALE IMAGE (NO STRETCH)
            # --------------------------------------------------
            img.thumbnail((label_w_px, label_h_px), Image.LANCZOS)

            canvas = Image.new(
                "RGB",
                (label_w_px, label_h_px),
                BACKGROUND_COLOR
            )

            x = (label_w_px - img.width) // 2
            y = (label_h_px - img.height) // 2
            canvas.paste(img, (x, y))

            # --------------------------------------------------
            # PRINT
            # --------------------------------------------------
            hdc.StartDoc(image_path.name)
            hdc.StartPage()

            dib = ImageWin.Dib(canvas)
            dib.draw(
                hdc.GetHandleOutput(),
                (0, 0, label_w_px, label_h_px)
            )

            hdc.EndPage()
            hdc.EndDoc()
            hdc.DeleteDC()

        finally:
            win32print.ClosePrinter(hPrinter)

    # --------------------------------------------------
    # PRINTER DISCOVERY
    # --------------------------------------------------

    def _find_printer(self) -> Optional[str]:
        printers = win32print.EnumPrinters(
            win32print.PRINTER_ENUM_LOCAL |
            win32print.PRINTER_ENUM_CONNECTIONS
        )

        if DEFAULT_PRINTER_NAME:
            for _, _, name, _ in printers:
                if name == DEFAULT_PRINTER_NAME and self._is_ready(name):
                    return name

        for _, _, name, _ in printers:
            lname = name.lower()
            if any(x in lname for x in EXCLUDED_PRINTERS):
                continue
            if self._is_ready(name):
                return name

        return None

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
