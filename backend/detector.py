# backend/detector.py
from datetime import datetime
import threading
import logging

from backend.model_watchdog import get_cached_model, register_listener

log = logging.getLogger(__name__)


class CycleDetector:
    """
    Industrial-grade cycle detector:
    Idle → Rising → Peak → Falling → Cycle End
    """

    def __init__(self, threshold=5.0, on_cycle_detected=None):
        self.threshold = float(threshold)
        self.on_cycle_detected = on_cycle_detected

        self.model_limits = {
            "model_id": None,
            "lower": 0.0,
            "upper": 100.0
        }

        self.buffer = []
        self.in_cycle = False
        self.peak_value = 0.0
        self.min_cycle_samples = 8

        self._apply_cached_model(get_cached_model())

    # --------------------------------------------------
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
                "📌 Detector Active Model → ID %s | %s–%s mm",
                model.get('id'),
                self.model_limits['lower'],
                self.model_limits['upper'],
            )
        except Exception as e:
                log.exception("⚠ detector: failed to apply cached model")

    # --------------------------------------------------
    def push(self, value: float):
        value = float(value)
        self.buffer.append(value)

        if not self.in_cycle and value > self.threshold:
            self.in_cycle = True
            self.peak_value = value
            return

        if self.in_cycle:
            if value > self.peak_value:
                self.peak_value = value

            if value <= self.threshold:
                self._finalize_cycle()

    # --------------------------------------------------
    def _finalize_cycle(self):
        if len(self.buffer) < self.min_cycle_samples:
            self._reset()
            return

        lower = self.model_limits["lower"]
        upper = self.model_limits["upper"]

        result = "PASS" if lower <= self.peak_value <= upper else "FAIL"

        model = get_cached_model()
        model_name = model.get("name", "Unknown")

        cycle_data = {
            "timestamp": datetime.now().isoformat(),
            "peak_height": round(self.peak_value, 2),
            "pass_fail": result,
            "model_id": self.model_limits.get("model_id"),
            "model_name": model_name
        }

        if self.on_cycle_detected:
            try:
                log.info("🔄 DETECTOR CYCLE: %s", cycle_data)
                self.on_cycle_detected(cycle_data)
            except Exception as e:
                log.exception("⚠ detector: callback error")

        self._reset()

    # --------------------------------------------------
    def _reset(self):
        self.buffer.clear()
        self.in_cycle = False
        self.peak_value = 0.0

    # --------------------------------------------------
    def update_model_limits(self, model: dict):
        if not model:
            return
        try:
            self.model_limits = {
                "model_id": model.get("id"),
                "lower": float(model.get("lower_limit", model.get("lower", 0))),
                "upper": float(model.get("upper_limit", model.get("upper", 100)))
            }
            log.info(
                "📌 detector:update_model_limits → ID %s | %s–%s mm",
                model.get('id'),
                self.model_limits['lower'],
                self.model_limits['upper'],
            )
        except Exception as e:
            log.exception("⚠ detector: update_model_limits failed")

    # --------------------------------------------------
    def update_threshold(self, value: float):
        self.threshold = float(value)
        log.info("📌 Detector threshold set to: %s", self.threshold)


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
            log.info("✅ Detector initialized.")
        else:
            detector.on_cycle_detected = on_cycle_detected


def push_laser_value(value):
    if detector:
        detector.push(value)

def update_threshold(value: float):
    """
    Module-level helper to update detector threshold.
    Kept for backward compatibility with main.py.
    """
    if detector:
        detector.update_threshold(value)
    else:
        log.warning("⚠ detector not initialized; threshold not applied")
