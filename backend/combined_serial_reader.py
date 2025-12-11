# backend/combined_serial_reader.py — FINAL PRODUCTION SAFE (PLC-GATED LASER)
# Reads BOTH Laser + PLC from ONE COM port (VSPE COM6)
# ✅ Laser is emitted ONLY when PLC = ON and RUNNING

import serial
import time
import threading
from PySide6.QtCore import QObject, Signal
from config.serial_ports import APP_READ_PORT, LASER_BAUD


class CombinedSerialReader(QObject):
    laser_value = Signal(float)
    plc_status = Signal(dict)
    status_changed = Signal(str)   # CONNECTED / DISCONNECTED

    def __init__(self):
        super().__init__()
        self.running = False
        self.serial = None
        self.thread = None
        self.last_data_time = 0

        # ✅ PLC GATING STATE
        self.plc_power = False
        self.plc_state = "OFFLINE"

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
                print(f"🔌 Connecting to Combined Stream on {APP_READ_PORT}...")

                self.serial = serial.Serial(
                    APP_READ_PORT,
                    LASER_BAUD,
                    timeout=0.2,
                    write_timeout=0.2
                )

                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.setDTR(True)
                self.serial.setRTS(True)

                self.status_changed.emit("CONNECTED")
                print(f"✅ Combined COM connected → {APP_READ_PORT}")

                self.last_data_time = time.time()

                while self.running:
                    try:
                        if self.serial.in_waiting > 0:
                            raw = self.serial.readline()
                            if not raw:
                                continue

                            line = raw.decode(errors="ignore").strip()
                            self.last_data_time = time.time()

                            # ✅ PLC STREAM (ALWAYS PROCESSED)
                            if line.startswith("PLC:"):
                                try:
                                    _, payload = line.split(":", 1)
                                    power, status = payload.split(",", 1)

                                    self.plc_power = (power == "ON")
                                    self.plc_state = status

                                    self.plc_status.emit({
                                        "power": self.plc_power,
                                        "status": self.plc_state
                                    })
                                except:
                                    pass

                            # ✅ LASER STREAM (ONLY WHEN PLC IS ON + RUNNING)
                            elif line.startswith("L"):
                                if self.plc_power and self.plc_state == "RUNNING":
                                    try:
                                        value = float(line[1:])
                                        self.laser_value.emit(value)
                                    except:
                                        pass
                                # ❌ Else: laser data is safely IGNORED

                        else:
                            # ✅ CRITICAL: Prevents 100% CPU busy-wait
                            time.sleep(0.01)

                        # ✅ Loss of stream detection
                        if time.time() - self.last_data_time > 5:
                            raise serial.SerialException("Combined stream timeout")

                    except Exception:
                        raise

            except Exception as e:
                print("❌ Combined COM disconnected:", e)
                self.status_changed.emit("DISCONNECTED")
                self._safe_close()
                time.sleep(1.5)

        self._safe_close()
        print("✅ Combined serial thread exited")

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
            print("⚠️ COM close warning:", e)

        self.serial = None

    # --------------------------------------------------
    def stop(self):
        print("🛑 Stopping Combined Serial Reader...")
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self._safe_close()


combined_reader = CombinedSerialReader()


def init_combined_reader():
    combined_reader.start()
