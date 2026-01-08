# backend/simulator.py
"""
Combined Pneumatic + PLC Simulator
Integrated as a backend service for automatic start/stop from main.py
Features:
- Realistic welding-aware laser simulation (25 Hz)
- Manual PLC control via console input
- Auto PLC mode
- Writes to virtual serial port (e.g., COM5 → VSPE → COM6)
"""

import logging
import random
import threading
from PySide6.QtCore import QThread, QObject, QTimer, Signal
import serial  # Imported inside run() to avoid issues if not needed

log = logging.getLogger(__name__)


class _SimulatorCore(QObject):
    send_laser = Signal(float)
    send_plc = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.running = True

        # Manual PLC override (starts in manual mode)
        self.manual_plc_enabled = True
        self.manual_power = "ON"
        self.manual_status = "RUNNING"

        # Laser simulation state machine
        self.state = "IDLE"
        self.value = 0.0
        self.peak = 0.0
        self.reference_height = 0.0
        self.weld_progress = 0.0
        self.hold_counter = 0
        self.idle_counter = random.randint(150, 400)

        # Laser timer @ 25 Hz (40 ms interval)
        self.laser_timer = QTimer()
        self.laser_timer.timeout.connect(self._generate_laser)
        self.laser_timer.start(40)

        # PLC auto-change timer (only active when not in manual)
        self.plc_timer = QTimer()
        self.plc_timer.timeout.connect(self._generate_plc_auto)
        self.plc_timer.start(random.randint(2000, 7000))

        # Manual input thread
        self.input_thread = threading.Thread(target=self._manual_plc_input, daemon=True)
        self.input_thread.start()

    def _generate_laser(self):
        if not self.running:
            return

        if self.state == "IDLE":
            # No part: near-zero with tiny noise
            self.value = round(random.uniform(0.0, 0.05), 2)
            self.idle_counter -= 1

            if self.idle_counter <= 0:
                self.peak = round(random.uniform(45.0, 90.0), 2)
                self.state = "RISING"
                self.idle_counter = random.randint(150, 400)

        elif self.state == "RISING":
            # Pneumatic cylinder pushing part up
            self.value += (self.peak - self.value) * 0.28

            if abs(self.value - self.peak) < 1.0:
                self.value = self.peak
                self.reference_height = self.peak
                self.weld_progress = 0.0
                self.hold_counter = random.randint(120, 220)
                self.state = "WELDING"

        elif self.state == "WELDING":
            # Real weld: material collapses slightly + vibration
            self.weld_progress += random.uniform(0.02, 0.08)

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

        elif self.state == "FALLING":
            # Pneumatic retract → part drops
            self.value *= 0.84
            if self.value < 3.0:
                self.value = 0.0
                self.state = "IDLE"

        # Emit current laser value
        self.send_laser.emit(self.value)

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

    def _manual_plc_input(self):
        print("\n✅ SIMULATOR: Manual PLC Control Active")
        print("   • Type: ON RUNNING | ON FAULT | OFF OFFLINE")
        print("   • Type: AUTO → switch to automatic PLC changes")
        print("   • Commands are case-insensitive\n")

        while self.running:
            try:
                cmd = input("PLC Command > ").strip().upper()
                if not cmd:
                    continue

                if cmd == "AUTO":
                    self.manual_plc_enabled = False
                    log.info("PLC switched to AUTO mode")
                    print("✅ PLC switched to AUTO mode")
                    continue

                parts = cmd.split()
                if len(parts) != 2:
                    print("❌ Invalid format. Use: ON RUNNING  or  OFF OFFLINE")
                    continue

                power, state = parts
                if power not in ("ON", "OFF"):
                    print("❌ First word must be ON or OFF")
                    continue

                self.manual_plc_enabled = True
                self.manual_power = power
                self.manual_status = state
                log.info("Manual PLC set to %s %s", power, state)
                print(f"✅ Manual PLC → {power} {state}")
                self.send_plc.emit(power, state)

            except EOFError:
                break
            except Exception as e:
                print(f"Input error: {e}")

    def stop(self):
        self.running = False
        self.laser_timer.stop()
        self.plc_timer.stop()
        # Thread will exit naturally due to daemon=True and running=False


class SimulatorThread(QThread):
    """Thread that opens serial port and runs the simulator core"""

    def __init__(self, port="COM5"):
        super().__init__()
        self.port = port

    def run(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=1
            )
            self.ser.flush()
            log.info("Simulator started on port %s", self.port)
            print(f"\n✅ Simulator started → Writing to {self.port} (VSPE → COM6)\n")
        except Exception as e:
            log.error("Failed to open serial port %s: %s", self.port, e)
            print(f"❌ Failed to open serial port {self.port}: {e}")
            return

        # Start simulation core
        self.core = _SimulatorCore()

        # Connect signals to serial writes
        self.core.send_laser.connect(lambda v: self._write(f"L{v:07.2f}\r\n"))
        self.core.send_plc.connect(lambda p, s: self._write(f"PLC:{p},{s}\r\n"))

        # Send initial PLC state after a short delay
        QTimer.singleShot(200, lambda: self.core.send_plc.emit(
            self.core.manual_power, self.core.manual_status
        ))

        # Run Qt event loop
        self.exec()

        # Cleanup on thread exit
        if hasattr(self, "ser"):
            self.ser.close()
            print("✅ Simulator → Serial port closed")

    def _write(self, data: str):
        try:
            if hasattr(self, "ser") and self.ser.is_open:
                self.ser.write(data.encode("ascii"))
                self.ser.flush()
        except Exception:
            pass

    def stop(self):
        """Gracefully stop the simulator and thread"""
        if hasattr(self, "core"):
            self.core.stop()
        self.quit()
        self.wait(3000)  # Wait up to 3 seconds for clean exit
        log.info("Simulator stopped")