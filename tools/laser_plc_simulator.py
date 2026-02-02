import serial
import time
import threading
import random
import sys

# =====================================================
# MODBUS ASCII CONFIG
# =====================================================
SLAVE_ID = "01"
FUNCTION = "03"
REGISTER = "1000"
BYTE_COUNT = "02"

BAUDRATE = 9600
BYTESIZE = serial.SEVENBITS
PARITY = serial.PARITY_EVEN
STOPBITS = serial.STOPBITS_ONE
TIMEOUT = 1.0

# =====================================================
# SCALING (MUST MATCH CombinedSerialReader)
# processed_mm = (raw * MULTIPLY) / DIVIDE
# =====================================================
MULTIPLY_FACTOR = 60.0
DIVIDE_FACTOR = 24573.0


def calculate_lrc(data_bytes: bytes) -> str:
    total = sum(data_bytes)
    lrc = (-total) & 0xFF
    return f"{lrc:02X}"


def laser_to_raw(laser_mm: float) -> int:
    return max(0, int((laser_mm * DIVIDE_FACTOR) / MULTIPLY_FACTOR))


# =====================================================
class LaserSimulator:
    """
    REALISTIC FAST PNEUMATIC LASER SIMULATOR
    (Per-cycle random weld depth)

    IDLE → FAST APPROACH → WELD (HOLD) → FAST RETRACT
    """

    POLL_INTERVAL = 0.10     # must match reader

    APPROACH_SPEED = 12.0   # mm / step
    RETRACT_SPEED = 14.0    # mm / step

    WELD_TIME = 5.5         # seconds ABOVE touch point (>=5 sec)
    IDLE_TIME = 2.0

    PEAK_DELTA_MIN = 2.0    # mm above TP
    PEAK_DELTA_MAX = 6.0    # mm above TP

    # -------------------------------------------------
    def __init__(self, port: str):
        self.port = port
        self.serial = None
        self.running = False

        self.touch_point = float(
            input("Enter TOUCH POINT (mm): ").strip()
        )

        self.laser_value = 0.0
        self.peak_height = self.touch_point
        self.phase = "IDLE"
        self.phase_start = time.time()

        print(
            f"\nSimulator configured:"
            f"\n  Touch Point : {self.touch_point:.2f} mm"
            f"\n  Weld Time   : {self.WELD_TIME:.2f} sec"
            f"\n  Peak Range  : +{self.PEAK_DELTA_MIN:.1f} → +{self.PEAK_DELTA_MAX:.1f} mm\n"
        )

    # -------------------------------------------------
    def start(self):
        self.serial = serial.Serial(
            port=self.port,
            baudrate=BAUDRATE,
            bytesize=BYTESIZE,
            parity=PARITY,
            stopbits=STOPBITS,
            timeout=TIMEOUT
        )

        self.running = True
        threading.Thread(target=self._worker, daemon=True).start()
        print(f"📡 Simulator listening on {self.port}")

    # -------------------------------------------------
    def _worker(self):
        buffer = b""

        while self.running:
            data = self.serial.read(1)
            if not data:
                time.sleep(0.01)
                continue

            buffer += data

            if buffer.endswith(b"\r\n"):
                frame = buffer.decode("ascii", errors="ignore").strip()
                buffer = b""

                if frame.startswith(":") and "0310000001" in frame:
                    self._update_physics()
                    raw = laser_to_raw(self.laser_value)
                    self.serial.write(
                        self._build_response(raw).encode("ascii")
                    )

    # -------------------------------------------------
    def _update_physics(self):
        now = time.time()

        # ---------------- IDLE ----------------
        if self.phase == "IDLE":
            self.laser_value = 0.0

            if now - self.phase_start >= self.IDLE_TIME:
                # 🎯 NEW RANDOM PEAK FOR EVERY CYCLE
                delta = random.uniform(
                    self.PEAK_DELTA_MIN,
                    self.PEAK_DELTA_MAX
                )
                self.peak_height = self.touch_point + delta

                print(
                    f"🔁 New cycle | Peak = {self.peak_height:.2f} mm "
                    f"(Depth = {delta:.2f} mm)"
                )

                self.phase = "APPROACH"
                self.phase_start = now

        # ---------------- FAST APPROACH ----------------
        elif self.phase == "APPROACH":
            self.laser_value += self.APPROACH_SPEED

            if self.laser_value >= self.touch_point + 0.3:
                self.phase = "WELD"
                self.phase_start = now

        # ---------------- WELD (HOLD AT PEAK) ----------------
        elif self.phase == "WELD":
            if now - self.phase_start <= self.WELD_TIME:
                # Stable pneumatic hold (realistic)
                self.laser_value = self.peak_height
            else:
                self.phase = "RETRACT"

        # ---------------- FAST RETRACT ----------------
        elif self.phase == "RETRACT":
            self.laser_value -= self.RETRACT_SPEED

            if self.laser_value <= 0.0:
                self.laser_value = 0.0
                self.phase = "IDLE"
                self.phase_start = now

    # -------------------------------------------------
    def _build_response(self, raw_value: int) -> str:
        payload = (
            SLAVE_ID +
            FUNCTION +
            BYTE_COUNT +
            f"{raw_value:04X}"
        )
        lrc = calculate_lrc(bytes.fromhex(payload))
        return f":{payload}{lrc}\r\n"

    # -------------------------------------------------
    def stop(self):
        self.running = False
        if self.serial and self.serial.is_open:
            self.serial.close()


# =====================================================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python laser_plc_simulator.py COM6")
        sys.exit(1)

    sim = LaserSimulator(sys.argv[1])
    sim.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping simulator...")
        sim.stop()
