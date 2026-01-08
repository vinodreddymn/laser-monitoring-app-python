# ======================================================
# PNEUMATIC + PLC SIMULATOR — FINAL v5 (WELDING-AWARE)
#
# ✅ Manual PLC Control
# ✅ CTRL+C Safe Shutdown
# ✅ Laser @ 25 Hz
# ✅ Realistic welding vibration + depth collapse
# Writes to COM5 → VSPE → COM6
# ======================================================

import sys
import random
import signal
import threading

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThread, QObject, QTimer, Signal


# ======================================================
# SIMULATOR CORE
# ======================================================
class _SimulatorCore(QObject):
    send_laser = Signal(float)
    send_plc   = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.running = True

        # -------------------------------
        # Manual PLC override
        # -------------------------------
        self.manual_plc_enabled = True
        self.manual_power = "ON"
        self.manual_status = "RUNNING"

        # -------------------------------
        # Laser simulation state machine
        # -------------------------------
        self.state = "IDLE"

        self.value = 0.0
        self.peak = 0.0

        self.reference_height = 0.0
        self.weld_progress = 0.0

        self.hold_counter = 0
        self.idle_counter = random.randint(150, 400)

        # -------------------------------
        # Laser timer (25 Hz)
        # -------------------------------
        self.laser_timer = QTimer()
        self.laser_timer.timeout.connect(self._generate_laser)
        self.laser_timer.start(40)

        # -------------------------------
        # PLC auto timer (disabled in manual)
        # -------------------------------
        self.plc_timer = QTimer()
        self.plc_timer.timeout.connect(self._generate_plc_auto)
        self.plc_timer.start(random.randint(2000, 7000))

        # -------------------------------
        # Manual PLC input thread
        # -------------------------------
        self.input_thread = threading.Thread(
            target=self._manual_plc_input,
            daemon=True
        )
        self.input_thread.start()

    # --------------------------------------------------
    # LASER SIGNAL GENERATION
    # --------------------------------------------------
    def _generate_laser(self):
        if not self.running:
            return

        # -------------------------------
        # IDLE: No part present
        # -------------------------------
        if self.state == "IDLE":
            self.value = round(random.uniform(0.0, 0.05), 2)
            self.idle_counter -= 1

            if self.idle_counter <= 0:
                self.peak = round(random.uniform(45.0, 90.0), 2)
                self.state = "RISING"
                self.idle_counter = random.randint(150, 400)

        # -------------------------------
        # RISING: Pneumatic push
        # -------------------------------
        elif self.state == "RISING":
            self.value += (self.peak - self.value) * 0.28

            if abs(self.value - self.peak) < 1.0:
                self.value = self.peak

                # Clamp reference height
                self.reference_height = self.peak

                # Reset welding dynamics
                self.weld_progress = 0.0
                self.hold_counter = random.randint(120, 220)

                self.state = "WELDING"

        # -------------------------------
        # WELDING: vibration + collapse
        # -------------------------------
        elif self.state == "WELDING":
            # Progressive downward collapse (true weld depth)
            self.weld_progress += random.uniform(0.02, 0.08)

            # Vibration components
            upward_vibration = random.uniform(0.0, 0.4)
            downward_vibration = random.uniform(0.2, 1.2)

            self.value = (
                self.reference_height
                - self.weld_progress
                + upward_vibration
                - downward_vibration
            )

            self.hold_counter -= 1
            if self.hold_counter <= 0:
                self.state = "FALLING"

        # -------------------------------
        # FALLING: Retract pneumatic
        # -------------------------------
        elif self.state == "FALLING":
            self.value *= 0.84
            if self.value < 3.0:
                self.value = 0.0
                self.state = "IDLE"

        self.send_laser.emit(self.value)

    # --------------------------------------------------
    # PLC AUTO MODE
    # --------------------------------------------------
    def _generate_plc_auto(self):
        if not self.running or self.manual_plc_enabled:
            return

        power = "ON" if random.random() < 0.92 else "OFF"
        status = (
            "OFFLINE"
            if power == "OFF"
            else random.choice(["RUNNING", "IDLE", "FAULT", "ALARM"])
        )

        self.send_plc.emit(power, status)

    # --------------------------------------------------
    # MANUAL PLC INPUT
    # --------------------------------------------------
    def _manual_plc_input(self):
        print("\n✅ MANUAL PLC INPUT ENABLED")
        print("👉 Type:  ON RUNNING | ON FAULT | OFF OFFLINE")
        print("👉 Type:  AUTO  → return to automatic PLC\n")

        while self.running:
            try:
                cmd = input().strip().upper()
                if not cmd:
                    continue

                if cmd == "AUTO":
                    self.manual_plc_enabled = False
                    print("✅ PLC set to AUTO mode")
                    continue

                parts = cmd.split()
                if len(parts) != 2:
                    print("❌ Invalid format. Use: ON RUNNING")
                    continue

                power, state = parts
                if power not in ("ON", "OFF"):
                    print("❌ Power must be ON or OFF")
                    continue

                self.manual_plc_enabled = True
                self.manual_power = power
                self.manual_status = state

                print(f"✅ Manual PLC → {power}, {state}")
                self.send_plc.emit(power, state)

            except Exception:
                pass

    # --------------------------------------------------
    def stop(self):
        self.running = False
        self.laser_timer.stop()
        self.plc_timer.stop()


# ======================================================
# SERIAL WRITER THREAD
# ======================================================
class SerialWriter(QThread):
    def __init__(self, port="COM5"):
        super().__init__()
        self.port = port

    def run(self):
        try:
            import serial
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=1
            )
            self.ser.flush()
            print(f"\n✅ Simulator → Writing to {self.port} → VSPE → COM6\n")
        except Exception as e:
            print(f"❌ Cannot open {self.port}: {e}")
            return

        # Core after serial open
        self.core = _SimulatorCore()

        self.core.send_laser.connect(
            lambda v: self._write(f"L{v:07.2f}\r\n")
        )
        self.core.send_plc.connect(
            lambda p, s: self._write(f"PLC:{p},{s}\r\n")
        )

        # Emit initial PLC state
        QTimer.singleShot(
            200,
            lambda: self.core.send_plc.emit(
                self.core.manual_power,
                self.core.manual_status
            )
        )

        self.exec()

        self.ser.close()
        print("✅ Simulator → Serial closed")

    def _write(self, text: str):
        try:
            self.ser.write(text.encode("ascii"))
            self.ser.flush()
        except Exception:
            pass

    def stop(self):
        if hasattr(self, "core"):
            self.core.stop()
        self.quit()
        self.wait(2000)


# ======================================================
# MAIN ENTRY
# ======================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)

    print("=" * 70)
    print("PNEUMATIC + PLC SIMULATOR — FINAL v5 (WELDING-AWARE)")
    print("Writes to COM5 → VSPE → COM6")
    print("Manual PLC + Welding Laser Simulation")
    print("CTRL+C SAFE SHUTDOWN ENABLED")
    print("=" * 70)

    writer = SerialWriter(port="COM5")
    writer.start()

    def cleanup():
        print("\n🛑 Stopping simulator...")
        writer.stop()

    app.aboutToQuit.connect(cleanup)

    def sigint_handler(sig, frame):
        print("\n🛑 Ctrl+C detected → Closing simulator cleanly...")
        app.quit()

    signal.signal(signal.SIGINT, sigint_handler)

    sys.exit(app.exec())
