from datetime import datetime
import threading
import logging
from statistics import mean

from backend.model_watchdog import get_cached_model, register_listener

log = logging.getLogger(__name__)


class CycleDetector:
    """
    Industrial Welding Cycle Detector (REFERENCE-GATED)

    ✔ Reference height locked first
    ✔ Welding depth measured ONLY after reference
    ✔ Retraction fully excluded
    ✔ No time or PLC dependency
    """

    # ============================
    # MACHINE PHYSICS CONSTANTS
    # ============================
    MAX_WELD_SLOPE = -2.0              # mm/sample
    MAX_PLAUSIBLE_WELD_DEPTH = 12.0    # mm
    MIN_WELD_SAMPLES = 6

    REFERENCE_STABLE_SLOPE = 0.4       # mm/sample
    REFERENCE_STABLE_COUNT = 5

    def __init__(self, threshold=1.0, on_cycle_detected=None):
        self.threshold = float(threshold)
        self.on_cycle_detected = on_cycle_detected

        self.model_limits = {
            "model_id": None,
            "lower": 0.0,
            "upper": 100.0
        }

        # ----------------------------
        # STATE
        # ----------------------------
        self.in_cycle = False
        self.reference_locked = False
        self.in_welding = False

        self.reference_height = None
        self.min_height = None
        self.max_height = None

        self.samples = []
        self.weld_samples = []

        self.prev_value = None
        self.reference_stable_counter = 0

        self._apply_cached_model(get_cached_model())

    # ============================
    # MODEL HANDLING
    # ============================
    def _apply_cached_model(self, model: dict):
        if not model:
            return
        try:
            self.model_limits = {
                "model_id": model.get("id"),
                "lower": float(model.get("lower_limit", 0)),
                "upper": float(model.get("upper_limit", 100))
            }
            log.info(
                "📌 Detector Model → ID %s | Depth %s–%s mm",
                model.get("id"),
                self.model_limits["lower"],
                self.model_limits["upper"],
            )
        except Exception:
            log.exception("⚠ detector: model apply failed")

    # ============================
    # MAIN INPUT
    # ============================
    def push(self, value: float):
        value = float(value)

        # ----------------------------
        # START CYCLE
        # ----------------------------
        if not self.in_cycle and value > self.threshold:
            self.in_cycle = True
            self.reference_locked = False
            self.in_welding = False

            self.samples.clear()
            self.weld_samples.clear()

            self.reference_height = None
            self.min_height = None
            self.max_height = None

            self.prev_value = value
            self.reference_stable_counter = 0

            self.samples.append(value)
            return

        if not self.in_cycle:
            return

        self.samples.append(value)

        # ----------------------------
        # SLOPE
        # ----------------------------
        slope = value - self.prev_value
        self.prev_value = value

        # ----------------------------
        # LOCK REFERENCE (CLAMP)
        # ----------------------------
        if not self.reference_locked:
            if abs(slope) < self.REFERENCE_STABLE_SLOPE:
                self.reference_stable_counter += 1
                if self.reference_stable_counter >= self.REFERENCE_STABLE_COUNT:
                    self.reference_height = value
                    self.reference_locked = True
                    self.in_welding = True

                    # Start weld tracking HERE
                    self.min_height = value
                    self.max_height = value
                    self.weld_samples.append(value)

                    log.debug("🔒 Reference locked at %.2f", value)
            else:
                self.reference_stable_counter = 0
            return  # ⛔ do NOT measure weld before reference

        # ----------------------------
        # WELDING WINDOW
        # ----------------------------
        if self.in_welding:
            # End welding if retraction detected
            if (
                slope < self.MAX_WELD_SLOPE or
                value < (self.reference_height - self.MAX_PLAUSIBLE_WELD_DEPTH)
            ):
                log.debug("🔻 Welding ended")
                self.in_welding = False
            else:
                self.weld_samples.append(value)

                if value < self.min_height:
                    self.min_height = value
                if value > self.max_height:
                    self.max_height = value

        # ----------------------------
        # END CYCLE
        # ----------------------------
        if not self.in_welding and value <= self.threshold:
            self._finalize_cycle()

    # ============================
    # FINALIZE
    # ============================
    def _finalize_cycle(self):
        if not self.reference_locked or len(self.weld_samples) < self.MIN_WELD_SAMPLES:
            log.debug("⚠ Cycle ignored (no valid weld)")
            self._reset()
            return

        weld_depth = round(self.reference_height - self.min_height, 2)

        lower = self.model_limits["lower"]
        upper = self.model_limits["upper"]
        result = "PASS" if lower <= weld_depth <= upper else "FAIL"

        model = get_cached_model() or {}
        model_name = model.get("name", "Unknown")
        model_type = model.get("model_type", "N/A")

        cycle_data = {
            "timestamp": datetime.now().isoformat(),
            "reference_height": round(self.reference_height, 2),
            "min_height": round(self.min_height, 2),
            "max_height": round(self.max_height, 2),
            "weld_depth": weld_depth,
            "peak_height": weld_depth,
            "pass_fail": result,
            "model_id": self.model_limits["model_id"],
            "model_name": model_name,
            "model_type": model_type
        }

        log.info("🔄 WELD CYCLE: %s", cycle_data)

        if self.on_cycle_detected:
            try:
                self.on_cycle_detected(cycle_data)
            except Exception:
                log.exception("⚠ detector callback error")

        self._reset()

    # ============================
    # RESET
    # ============================
    def _reset(self):
        self.in_cycle = False
        self.in_welding = False
        self.reference_locked = False

        self.samples.clear()
        self.weld_samples.clear()

        self.reference_height = None
        self.min_height = None
        self.max_height = None
        self.prev_value = None
        self.reference_stable_counter = 0

    # ============================
    # RUNTIME UPDATES
    # ============================
    def update_model_limits(self, model: dict):
        if model:
            self.model_limits = {
                "model_id": model.get("id"),
                "lower": float(model.get("lower_limit", 0)),
                "upper": float(model.get("upper_limit", 100))
            }

    def update_threshold(self, value: float):
        self.threshold = float(value)


# ======================================================
# GLOBAL INSTANCE
# ======================================================
detector = None
_detector_lock = threading.Lock()


def init_detector(on_cycle_detected):
    global detector
    with _detector_lock:
        if detector is None:
            detector = CycleDetector(on_cycle_detected=on_cycle_detected)
            register_listener(detector.update_model_limits)
            detector.update_threshold(1.0)
            log.info("✅ Welding Depth Detector initialized.")
        else:
            detector.on_cycle_detected = on_cycle_detected


def push_laser_value(value):
    if detector:
        detector.push(value)


def update_threshold(value: float):
    if detector:
        detector.update_threshold(value)
