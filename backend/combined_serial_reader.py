# ============================================================
# Combined Serial Reader – FINAL PRODUCTION SAFE
#
# - Reads PLC + Laser from ONE COM port (VSPE / physical)
# - PLC status ALWAYS processed
# - Laser data ONLY emitted when:
#     PLC power = ON AND PLC state = RUNNING
# - Safe when simulator is started BEFORE application
# - Auto reconnect + watchdog timeout
# ============================================================

import serial
import time
import threading
import logging

from PySide6.QtCore import QObject, Signal
from config.serial_ports import APP_READ_PORT, LASER_BAUD

log = logging.getLogger(__name__)


class CombinedSerialReader(QObject):
    # ----------------- Qt Signals -----------------
    laser_value = Signal(float)
    plc_status = Signal(dict)
    status_changed = Signal(str)   # CONNECTED / DISCONNECTED

    # --------------------------------------------------
    def __init__(self):
        super().__init__()

        self.running = False
        self.thread = None
        self.serial = None

        self.last_data_time = 0

        # -------- PLC STATE (GATING) --------
        self.plc_power = False
        self.plc_state = "OFFLINE"
        self.plc_synced = False   # 🔑 Critical for late-start sync

    # --------------------------------------------------
    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(
            target=self._worker,
            daemon=True
        )
        self.thread.start()

    # --------------------------------------------------
    def _worker(self):
        while self.running:
            try:
                log.info("🔌 Connecting to Combined COM → %s", APP_READ_PORT)

                self.serial = serial.Serial(
                    port=APP_READ_PORT,
                    baudrate=LASER_BAUD,
                    timeout=0.2,
                    write_timeout=0.2
                )

                # Clean startup
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.setDTR(True)
                self.serial.setRTS(True)

                # Reset sync state on every connect
                self.plc_synced = False
                self.plc_power = False
                self.plc_state = "OFFLINE"

                self.last_data_time = time.time()

                self.status_changed.emit("CONNECTED")
                log.info("✅ Combined COM connected")

                # ================== READ LOOP ==================
                while self.running:
                    if self.serial.in_waiting > 0:
                        raw = self.serial.readline()
                        if not raw:
                            continue

                        line = raw.decode(errors="ignore").strip()
                        self.last_data_time = time.time()

                        # ---------------- PLC STREAM ----------------
                        if line.startswith("PLC:"):
                            self._handle_plc_line(line)

                        # ---------------- LASER STREAM --------------
                        elif line.startswith("L"):
                            self._handle_laser_line(line)

                    else:
                        # Prevent busy loop
                        time.sleep(0.01)

                    # ----------- Watchdog timeout -----------
                    if time.time() - self.last_data_time > 5:
                        raise serial.SerialException(
                            "Combined stream timeout"
                        )

            except Exception as e:
                log.exception("❌ Combined COM error: %s", e)
                self.status_changed.emit("DISCONNECTED")
                self._safe_close()
                time.sleep(1.5)

        self._safe_close()
        log.info("🛑 Combined serial thread exited")

    # --------------------------------------------------
    def _handle_plc_line(self, line: str):
        """
        Expected format:
        PLC:ON,RUNNING
        PLC:OFF,STOPPED
        """
        try:
            _, payload = line.split(":", 1)
            power, state = payload.split(",", 1)

            self.plc_power = (power.strip() == "ON")
            self.plc_state = state.strip()
            self.plc_synced = True   # 🔑 Sync achieved

            self.plc_status.emit({
                "power": self.plc_power,
                "status": self.plc_state
            })

        except Exception:
            log.debug("⚠ Invalid PLC frame ignored: %s", line)

    # --------------------------------------------------
    def _handle_laser_line(self, line: str):
        """
        Expected format:
        L52.43
        """
        if not self.plc_synced:
            return

        if not (self.plc_power and self.plc_state == "RUNNING"):
            return

        try:
            value = float(line[1:])
            self.laser_value.emit(value)
        except Exception:
            log.debug("⚠ Invalid laser frame ignored: %s", line)

    # --------------------------------------------------
    def _safe_close(self):
        try:
            if self.serial:
                try:
                    self.serial.reset_input_buffer()
                    self.serial.reset_output_buffer()
                except Exception:
                    pass

                if self.serial.is_open:
                    try:
                        self.serial.setDTR(False)
                        self.serial.setRTS(False)
                    except Exception:
                        pass
                    self.serial.close()

                del self.serial
        except Exception as e:
            log.warning("⚠ COM close warning: %s", e)

        self.serial = None

    # --------------------------------------------------
    def stop(self):
        log.info("🛑 Stopping Combined Serial Reader...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        self._safe_close()


# ============================================================
# Singleton instance
# ============================================================
combined_reader = CombinedSerialReader()


def init_combined_reader():
    combined_reader.start()
