# ============================================================
# Combined Serial Reader – LASER FROM D0 (Modbus ONLY)
# FLOAT (REAL) from D0 + D1
# COMPATIBLE WITH YOUR EXISTING main.py & signals.py
# ============================================================

import serial
import time
import threading
import logging
import struct

from PySide6.QtCore import QObject, Signal
from config.app_config import APP_READ_PORT

log = logging.getLogger(__name__)


class CombinedSerialReader(QObject):
    # ────────────────────────────────────────────────
    # Signals — EXACTLY matching what main.py expects
    # ────────────────────────────────────────────────
    laser_value    = Signal(float)        # laser value (FLOAT)
    plc_status     = Signal(dict)         # {"power": bool, "status": str}
    status_changed = Signal(str)          # "CONNECTED" / "DISCONNECTED"

    def __init__(self):
        super().__init__()

        self.running = False
        self.thread = None
        self.serial = None

        # Modbus config
        self.modbus_slave = '01'
        self.d0_addr = '1000'              # D0 start address
        self.poll_interval = 0.5
        self.watchdog_d0 = 6.0

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

    # ────────────────────────────────────────────────
    # READ FLOAT (REAL) FROM D0 + D1
    # ────────────────────────────────────────────────
    def _poll_d0(self) -> float | None:
        if not self.serial or not self.serial.is_open:
            return None

        try:
            # Read 2 registers (FLOAT = 32-bit)
            message = self.modbus_slave + '03' + self.d0_addr + '0002'
            msg_bytes = bytes.fromhex(message)
            lrc = self._calculate_lrc(msg_bytes)
            frame = ':' + message + lrc + '\r\n'

            self.serial.reset_input_buffer()
            self.serial.write(frame.encode('ascii'))
            self.serial.flush()

            raw = self.serial.read(64)
            if not raw:
                return None

            text = raw.decode('ascii', errors='replace').rstrip('\r\n')
            if not text.startswith(':'):
                return None

            content = text[1:]

            # Validate response
            if content[:2] != self.modbus_slave:
                return None
            if content[2:4] != '03':
                return None
            if content[4:6] != '04':        # 4 data bytes for FLOAT
                return None

            # Extract words
            high_word = int(content[6:10], 16)
            low_word  = int(content[10:14], 16)

            # Big-endian FLOAT (most PLCs, incl. Siemens)
            raw_32 = (high_word << 16) | low_word
            value = struct.unpack('>f', raw_32.to_bytes(4, 'big'))[0]

            # Sanity check (optional but recommended)
            if not (-1e6 < value < 1e6):
                return None

            return value

        except Exception:
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
                self.plc_status.emit({"power": True, "status": "RUNNING"})

                while self.running:
                    now = time.time()

                    if now - self.last_poll_time >= self.poll_interval:
                        value = self._poll_d0()

                        if value is not None:
                            self.laser_value.emit(value)
                            self.last_valid_d0_time = now
                            self.d0_success_count += 1
                            self.d0_fail_count = 0

                            self.plc_status.emit(
                                {"power": True, "status": "RUNNING"}
                            )
                        else:
                            self.d0_fail_count += 1
                            if self.d0_fail_count >= 6:
                                self.plc_status.emit(
                                    {"power": False, "status": "TIMEOUT"}
                                )

                        self.last_poll_time = now

                    time.sleep(0.02)

                    # Watchdog
                    if now - self.last_valid_d0_time > self.watchdog_d0:
                        self.plc_status.emit(
                            {"power": False, "status": "OFFLINE"}
                        )
                        self.status_changed.emit("DISCONNECTED")

            except Exception as e:
                log.exception(
                    "PLC Modbus error on %s: %s", APP_READ_PORT, e
                )
                self.status_changed.emit("DISCONNECTED")
                self.plc_status.emit(
                    {"power": False, "status": "DISCONNECTED"}
                )
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
