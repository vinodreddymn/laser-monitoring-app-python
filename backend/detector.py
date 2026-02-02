# backend/detector.py

from datetime import datetime
import threading
import logging

from backend.model_watchdog import get_cached_model, register_listener

log = logging.getLogger(__name__)


class CycleDetector:
    """
    Pneumatic Welding Cycle Detector (Touch-Point Gated)

    Cycle definition:
    -----------------
    • START  → laser crosses ABOVE touch point
    • PEAK   → maximum laser value during cycle
    • END    → laser crosses BELOW touch point
    • Weld Depth = peak_height − touch_point
    """

    MIN_SAMPLES_IN_CYCLE = 5
    TP_HYSTERESIS = 0.05  # mm (prevents chatter)

    # --------------------------------------------------
    def __init__(self, on_cycle_detected=None):
        self.on_cycle_detected = on_cycle_detected

        # ---------------- Model ----------------
        self.model = {}
        self.touch_point = 0.0
        self.lower_limit = 0.0
        self.upper_limit = 100.0

        # ---------------- State ----------------
        self.in_cycle = False
        self.peak_height = 0.0
        self.sample_count = 0
        self.prev_value = 0.0  # NEVER None

        # Load model + subscribe to updates
        self._apply_model(get_cached_model())
        register_listener(self._apply_model)

    # ==================================================
    # MODEL UPDATE
    # ==================================================
    def _apply_model(self, model: dict):
        if not model:
            return

        try:
            self.model = model
            self.touch_point = float(model.get("touch_point", 0.0))
            self.lower_limit = float(model.get("lower_limit", 0.0))
            self.upper_limit = float(model.get("upper_limit", 100.0))

            log.info(
                "📌 Detector Model → %s | TP=%.2f | Limits %.2f–%.2f",
                model.get("name"),
                self.touch_point,
                self.lower_limit,
                self.upper_limit,
            )
        except Exception:
            log.exception("⚠ detector: model apply failed")

    # ==================================================
    # MAIN INPUT
    # ==================================================
    def push(self, value: float):
        value = float(value)

        tp_high = self.touch_point + self.TP_HYSTERESIS
        tp_low = self.touch_point - self.TP_HYSTERESIS

        # ---------- START ----------
        if not self.in_cycle:
            if self.prev_value < tp_high and value >= tp_high:
                self._start_cycle(value)

            self.prev_value = value
            return

        # ---------- IN CYCLE ----------
        self.sample_count += 1

        if value > self.peak_height:
            self.peak_height = value

        # ---------- END ----------
        if self.prev_value > tp_low and value <= tp_low:
            self._end_cycle()

        self.prev_value = value

    # ==================================================
    # CYCLE HANDLING
    # ==================================================
    def _start_cycle(self, value: float):
        self.in_cycle = True
        self.sample_count = 1
        self.peak_height = value

        log.info(
            "▶ Cycle START | TP=%.2f | value=%.2f",
            self.touch_point,
            value,
        )

    def _end_cycle(self):
        if self.sample_count < self.MIN_SAMPLES_IN_CYCLE:
            log.warning("⚠ Cycle ignored (too short / noise)")
            self._reset()
            return

        weld_depth = round(self.peak_height - self.touch_point, 2)

        result = (
            "PASS"
            if self.lower_limit <= weld_depth <= self.upper_limit
            else "FAIL"
        )

        cycle_data = {
            # ---------- lifecycle ----------
            "timestamp": datetime.now().isoformat(),
            "completed": True,

            # ---------- measurements ----------
            "touch_point": round(self.touch_point, 2),
            "peak_height": round(self.peak_height, 2),
            "weld_depth": weld_depth,

            # ---------- result ----------
            "pass_fail": result,

            # ---------- model ----------
            "model_id": self.model.get("id"),
            "model_name": self.model.get("name", "Unknown"),
            "model_type": self.model.get("model_type", "N/A"),
        }

        log.info("🔄 CYCLE END → %s", cycle_data)

        if self.on_cycle_detected:
            try:
                self.on_cycle_detected(cycle_data)
            except Exception:
                log.exception("⚠ detector callback failed")

        self._reset()

    # ==================================================
    # RESET
    # ==================================================
    def _reset(self):
        self.in_cycle = False
        self.peak_height = 0.0
        self.sample_count = 0
        # ❗ prev_value intentionally preserved


# ======================================================
# GLOBAL INSTANCE (thread-safe)
# ======================================================
detector = None
_detector_lock = threading.Lock()


def init_detector(on_cycle_detected):
    global detector
    with _detector_lock:
        if detector is None:
            detector = CycleDetector(on_cycle_detected=on_cycle_detected)
            log.info("✅ Touch-point detector initialized")
        else:
            detector.on_cycle_detected = on_cycle_detected


def push_laser_value(value: float):
    if detector:
        detector.push(value)


def update_threshold(value: float):
    """
    Backward-compatibility stub.
    Touch-point logic does not use thresholds.
    """
    log.debug(
        "ℹ update_threshold(%.2f) ignored — touch-point logic active",
        value
    )
