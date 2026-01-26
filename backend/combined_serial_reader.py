# ============================================================
# Combined Serial Reader – LASER FROM D0 (Modbus ONLY)
# COMPATIBLE WITH YOUR EXISTING main.py & signals.py
# ============================================================

import serial
import time
import threading
import logging

from PySide6.QtCore import QObject, Signal
from config.app_config import APP_READ_PORT

log = logging.getLogger(__name__)


class CombinedSerialReader(QObject):
    # ────────────────────────────────────────────────
    # Signals — EXACTLY matching what main.py expects
    # ────────────────────────────────────────────────
    laser_value    = Signal(float)        # scaled laser value → GUI + detector
    plc_status     = Signal(dict)         # ← ADDED BACK: {"power": bool, "status": str}
    status_changed = Signal(str)          # "CONNECTED" / "DISCONNECTED"

    # Optional extra (you can ignore if not used)
    plc_d0_raw     = Signal(int)

    def __init__(self):
        super().__init__()

        self.running = False
        self.thread = None
        self.serial = None

        # Modbus config
        self.modbus_slave = '01'
        self.d0_addr = '1000'
        self.poll_interval = 0.5           # how often to read D0
        self.watchdog_d0 = 6.0             # timeout if no valid read

        # Scaling: adjust if needed (e.g. 100.0 → 1234 → 12.34)
        self.scale_factor = 1.0

        self.last_valid_d0_time = time.time()
        self.last_poll_time = 0
        self.d0_success_count = 0
        self.d0_fail_count = 0

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    def _calculate_lrc(self, data_bytes: bytes) -> str:
        total = sum(data_bytes)
        lrc = (-total) & 0xFF
        return f'{lrc:02X}'.upper()

    def _poll_d0(self) -> int | None:
        if not self.serial or not self.serial.is_open:
            return None
        try:
            message = self.modbus_slave + '03' + self.d0_addr + '0001'
            msg_bytes = bytes.fromhex(message)
            lrc = self._calculate_lrc(msg_bytes)
            frame = ':' + message + lrc + '\r\n'

            self.serial.reset_input_buffer()
            self.serial.write(frame.encode('ascii'))
            self.serial.flush()

            raw = self.serial.read(50)
            if not raw:
                return None

            text = raw.decode('ascii', errors='replace').rstrip('\r\n')
            if text.startswith(':') and len(text) >= 11:
                content = text[1:]
                if (content[:2] == self.modbus_slave and
                    content[2:4] == '03' and content[4:6] == '02'):
                    value_hex = content[6:10]
                    try:
                        return int(value_hex, 16)
                    except ValueError:
                        pass
        except Exception:
            pass
        return None

    def _worker(self):
        while self.running:
            try:
                log.info("Connecting to PLC Modbus on %s ...", APP_READ_PORT)

                self.serial = serial.Serial(
                    port=APP_READ_PORT,
                    baudrate=9600,
                    bytesize=serial.SEVENBITS,
                    parity=serial.PARITY_EVEN,
                    stopbits=serial.STOPBITS_ONE,
                    timeout=0.5
                )

                log.info("PLC Modbus connected on %s", APP_READ_PORT)

                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.setDTR(True)
                self.serial.setRTS(True)

                self.last_valid_d0_time = time.time()
                self.last_poll_time = 0
                self.d0_success_count = 0
                self.d0_fail_count = 0

                self.status_changed.emit("CONNECTED")
                # Emit initial PLC status — matches what your GUI expects
                self.plc_status.emit({"power": True, "status": "RUNNING"})

                while self.running:
                    now = time.time()

                    if now - self.last_poll_time >= self.poll_interval:
                        raw_d0 = self._poll_d0()
                        if raw_d0 is not None:
                            self.plc_d0_raw.emit(raw_d0)
                            scaled = raw_d0 / self.scale_factor
                            self.laser_value.emit(scaled)
                            self.last_valid_d0_time = now
                            self.d0_success_count += 1
                            self.d0_fail_count = 0

                            # Tell GUI: PLC is connected and running
                            self.plc_status.emit({"power": True, "status": "RUNNING"})
                        else:
                            self.d0_fail_count += 1
                            if self.d0_fail_count >= 6:
                                # PLC looks disconnected
                                self.plc_status.emit({"power": False, "status": "TIMEOUT"})
                        self.last_poll_time = now

                    time.sleep(0.02)

                    # Watchdog — if no valid D0 for too long
                    if now - self.last_valid_d0_time > self.watchdog_d0:
                        self.plc_status.emit({"power": False, "status": "OFFLINE"})
                        self.status_changed.emit("DISCONNECTED")

            except Exception as e:
                log.exception("PLC Modbus error on %s: %s", APP_READ_PORT, e)
                self.status_changed.emit("DISCONNECTED")
                self.plc_status.emit({"power": False, "status": "DISCONNECTED"})
                self._safe_close()
                time.sleep(2.0)

        self._safe_close()
        log.info("Combined serial reader stopped")

    def _safe_close(self):
        if self.serial:
            try:
                if self.serial.is_open:
                    self.serial.close()
                log.info("Closed %s", APP_READ_PORT)
            except Exception as e:
                log.warning("Close error: %s", e)
            self.serial = None

    def stop(self):
        log.info("Stopping reader...")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
        self._safe_close()


# Singleton — unchanged
combined_reader = CombinedSerialReader()

def init_combined_reader():
    combined_reader.start()