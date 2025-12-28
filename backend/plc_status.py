# ======================================================
# backend/plc_status.py
# FINAL – Industrial Safe PLC Status Listener (Windows)
# ======================================================

from PySide6.QtCore import QObject, QThread, Signal
import serial
import re
import time
import json
import logging
from pathlib import Path

from config.app_config import (
    DEFAULT_BAUD_PLC,
    SERIAL_TIMEOUT,
    SERIAL_WRITE_TIMEOUT,
    PLC_POLL_INTERVAL
)

log = logging.getLogger(__name__)

# ======================================================
# CONFIG
# ======================================================

CONFIG_FILE = Path(__file__).parent / "peripherals_config.json"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"plc_port": "COM6"}

config = load_config()

PLC_PORT = config.get("plc_port", "COM6")
PLC_BAUD = DEFAULT_BAUD_PLC


# ======================================================
# WORKER (runs in QThread)
# ======================================================

class _PLCWorker(QObject):
    status_ready = Signal(dict)

    def __init__(self, port: str):
        super().__init__()
        self.port = port
        self.running = False
        self.ser = None

    # --------------------------------------------------
    def run(self):
        self.running = True
        pattern = re.compile(r"PLC:(ON|OFF),(\w+)")

        while self.running:
            try:
                log.info("🔌 Connecting to PLC on %s", self.port)

                self.ser = serial.Serial(
                    self.port,
                    PLC_BAUD,
                    timeout=SERIAL_TIMEOUT,
                    write_timeout=SERIAL_WRITE_TIMEOUT
                )

                # ✅ Windows COM stabilization
                self.ser.reset_input_buffer()
                self.ser.reset_output_buffer()
                self.ser.setDTR(True)
                self.ser.setRTS(True)

                log.info("🟢 PLC connected")

                while self.running and self.ser and self.ser.is_open:
                    if self.ser.in_waiting > 0:
                        line = self.ser.readline().decode(
                            errors="ignore"
                        ).strip()

                        if not line:
                            continue

                        match = pattern.search(line)
                        if match:
                            self.status_ready.emit({
                                "power": match.group(1) == "ON",
                                "status": match.group(2)
                            })

                    time.sleep(0.05)

            except Exception as e:
                log.error("🔴 PLC error: %s", e)
                self._safe_close()
                time.sleep(1.5)

        self._safe_close()
        log.info("🛑 PLC worker stopped")

    # --------------------------------------------------
    def _safe_close(self):
        try:
            if self.ser:
                try:
                    self.ser.reset_input_buffer()
                    self.ser.reset_output_buffer()
                except Exception:
                    pass

                if self.ser.is_open:
                    self.ser.setDTR(False)
                    self.ser.setRTS(False)
                    self.ser.close()
        except Exception as e:
            log.warning("⚠️ PLC close warning: %s", e)

        self.ser = None

    # --------------------------------------------------
    def stop(self):
        self.running = False
        self._safe_close()


# ======================================================
# LISTENER (UI-facing)
# ======================================================

class PLCListener(QObject):
    """
    Public API:
    - plc_status_changed(dict)
    - emit_current_status()
    - start() / stop()
    """

    plc_status_changed = Signal(dict)

    def __init__(self):
        super().__init__()

        self.last_status = {
            "power": False,
            "status": "OFFLINE"
        }

        self.thread = QThread(self)
        self.worker = _PLCWorker(PLC_PORT)
        self.worker.moveToThread(self.thread)

        self.worker.status_ready.connect(self._on_status_ready)
        self.thread.started.connect(self.worker.run)

    # --------------------------------------------------
    def _on_status_ready(self, status: dict):
        self.last_status = status
        self.plc_status_changed.emit(status)

    # --------------------------------------------------
    def emit_current_status(self):
        self.plc_status_changed.emit(self.last_status)

    # --------------------------------------------------
    def start(self):
        if not self.thread.isRunning():
            self.thread.start()
            log.info("PLC listener started")

    # --------------------------------------------------
    def stop(self):
        log.info("Stopping PLC listener...")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait(2000)


# ======================================================
# SINGLETON
# ======================================================

plc_listener = PLCListener()
