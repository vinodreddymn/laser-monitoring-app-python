import serial
import time
import threading
from PySide6.QtCore import QObject, Signal
from config.app_config import APP_READ_PORT, LASER_BAUD
import logging

log = logging.getLogger(__name__)


class LaserReader(QObject):
    value_received = Signal(float)
    status_changed = Signal(str)   # "CONNECTED", "DISCONNECTED"

    READ_INTERVAL = 0.3    # ✅ ONLY UI EMISSION throttle (NOT hardware read)
    TIMEOUT_LIMIT = 3.0

    def __init__(self):
        super().__init__()
        self.running = False
        self.serial = None
        self.thread = None
        self.last_data_time = 0
        self.last_emit_time = 0    # ✅ FIX: emit throttle only

    # --------------------------------------------------
    def start(self):
        if self.running:
            return

        self.running = True
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    # --------------------------------------------------
    def _worker(self):
        while self.running:
            try:
                log.info("🔌 Connecting to Laser on %s...", APP_READ_PORT)

                self.serial = serial.Serial(
                    APP_READ_PORT,
                    LASER_BAUD,
                    timeout=0.2,
                    write_timeout=0.2
                )

                # ✅ WINDOWS DRIVER HARD RESET
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.setDTR(True)
                self.serial.setRTS(True)

                self.status_changed.emit("CONNECTED")
                log.info("✅ Laser connected → %s", APP_READ_PORT)

                self.last_data_time = time.time()
                self.last_emit_time = 0

                while self.running:
                    try:
                        # ✅ ALWAYS READ HARDWARE IMMEDIATELY
                        if self.serial.in_waiting > 0:
                            raw = self.serial.readline()

                            if raw:
                                data = raw.decode(errors="ignore").strip()
                                if data:
                                    value = float(data.split(",")[-1])
                                    now = time.time()

                                    self.last_data_time = now

                                    # ✅ THROTTLE ONLY THE GUI EMIT
                                    if now - self.last_emit_time >= self.READ_INTERVAL:
                                        self.last_emit_time = now
                                        self.value_received.emit(value)

                        # ✅ DEVICE LOSS DETECTION
                        if time.time() - self.last_data_time > self.TIMEOUT_LIMIT:
                            raise serial.SerialException("Laser timeout")

                        time.sleep(0.005)   # ✅ CPU protection

                    except Exception:
                        raise

            except Exception as e:
                log.exception("❌ Laser disconnected: %s", e)
                self.status_changed.emit("DISCONNECTED")
                self._safe_close()
                time.sleep(1.5)

        self._safe_close()
        log.info("✅ Laser reader thread exited cleanly")

    # --------------------------------------------------
    def _safe_close(self):
        try:
            if self.serial:
                try:
                    self.serial.reset_input_buffer()
                    self.serial.reset_output_buffer()
                except:
                    pass

                if self.serial.is_open:
                    self.serial.setDTR(False)
                    self.serial.setRTS(False)
                    self.serial.close()

                del self.serial

        except Exception as e:
            log.warning("⚠️ COM close warning: %s", e)

        self.serial = None

    # --------------------------------------------------
    def stop(self):
        log.info("🛑 Stopping Laser Reader...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)

        self._safe_close()


laser_reader = LaserReader()


def init_laser_reader():
    laser_reader.start()
