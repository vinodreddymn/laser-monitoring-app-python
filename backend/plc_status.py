# backend/plc_status.py — FINAL INDUSTRIAL SAFE VERSION (WINDOWS FIXED)

from PySide6.QtCore import QThread, Signal, QObject
import serial, re, time
from config.serial_ports import APP_READ_PORT, PLC_BAUD


class _PLCWorker(QObject):
    status_ready = Signal(dict)

    def __init__(self, port):
        super().__init__()
        self.port = port
        self.running = False
        self.serial = None

    # --------------------------------------------------
    def run(self):
        self.running = True
        pattern = re.compile(r'PLC:(ON|OFF),(\w+)')

        while self.running:
            try:
                print(f"🔌 Connecting to PLC on {self.port}...")

                self.serial = serial.Serial(
                    self.port,
                    PLC_BAUD,
                    timeout=0.2,
                    write_timeout=0.2
                )

                # ✅ HARD DRIVER RESET (WINDOWS FIX)
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self.serial.setDTR(True)
                self.serial.setRTS(True)

                print(f"✅ PLC connected → {self.port}")

                while self.running:
                    try:
                        if self.serial.in_waiting > 0:
                            line = self.serial.readline().decode(errors='ignore').strip()
                            if not line:
                                continue

                            m = pattern.search(line)
                            if m:
                                self.status_ready.emit({
                                    "power": m.group(1) == "ON",
                                    "status": m.group(2)
                                })

                    except Exception:
                        raise   # force reconnect + cleanup

            except Exception as e:
                print("❌ PLC disconnected:", e)
                self._safe_close()
                time.sleep(1.5)

        # ✅ FINAL CLEAN EXIT
        self._safe_close()
        print("✅ PLC thread exited cleanly")

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
            print("⚠️ PLC COM close warning:", e)

        self.serial = None

    # --------------------------------------------------
    def stop(self):
        print("🛑 Stopping PLC Worker...")
        self.running = False
        self._safe_close()


class PLCListener(QObject):
    status_updated = Signal(dict)

    def __init__(self):
        super().__init__()
        self.thread = QThread()
        self.worker = _PLCWorker(APP_READ_PORT)
        self.worker.moveToThread(self.thread)

        self.worker.status_ready.connect(self.status_updated)
        self.thread.started.connect(self.worker.run)

    def start(self):
        if not self.thread.isRunning():
            self.thread.start()

    def stop(self):
        print("🛑 Stopping PLC Listener...")
        self.worker.stop()
        self.thread.quit()
        self.thread.wait(2000)


plc_listener = PLCListener()


def init_plc_listener(callback):
    plc_listener.status_updated.connect(callback)
    plc_listener.start()
