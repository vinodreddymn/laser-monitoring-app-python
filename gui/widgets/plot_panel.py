import time
import logging
from typing import List, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

import pyqtgraph as pg
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QGraphicsPixmapItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap

log = logging.getLogger(__name__)


class PlotPanel(QFrame):
    """
    Industrial Welding Laser Plot (Clarity-First)

    ✔ Raw laser waveform
    ✔ Large PASS / FAIL + depth annotation (no vertical overlays)
    ✔ Left-aligned cycle labels on waveform
    ✔ Overlays move with time axis
    ✔ Branding watermark always visible
    ✔ Clean supervisor badge
    """


    TIME_WINDOW_SEC = 60
    MAX_POINTS = 900
    UPDATE_INTERVAL_MS = 100
    MAX_CYCLE_OVERLAYS = 6   # keep display clean

    # --------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------- Live Data ----------------
        self.data: List[Tuple[float, float]] = []

        # ---------------- Model Info ----------------
        self.model_name = ""
        self.model_type = ""
        self.lower_limit = 0.0
        self.upper_limit = 0.0

        # ---------------- Cycle Overlays ----------------
        self._cycle_overlays = []

        # ---------------- Throttle ----------------
        self._pending_update = False
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._apply_update)

        self._build_ui()

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background:#0b111b;
                border:1px solid #30363d;
                border-radius:8px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ---------------- Plot ----------------
        self.plot = pg.PlotWidget(background="#0b111b")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setMouseEnabled(False, False)
        self.plot.enableAutoRange(False, False)

        self.plot.getAxis("bottom").setTicks([])
        self.plot.getAxis("bottom").setPen("#0b111b")

        y_axis = self.plot.getAxis("left")
        y_axis.setLabel("Laser Height (mm)")
        y_axis.label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        y_axis.setTextPen("#e6edf3")

        self.curve = self.plot.plot(
            pen=pg.mkPen("#00ff99", width=3)
        )

        self._install_watermark(
            image_path="assets/watermark.png",
            opacity=0.08,
            scale_ratio=0.75
        )

        # ---------------- Badge ----------------
        self.badge = QLabel("")
        self.badge.setAlignment(Qt.AlignCenter)
        self.badge.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.badge.setStyleSheet("""
            QLabel {
                background:#0f1622;
                border:1px solid #2d3b4f;
                border-radius:8px;
                padding:10px;
                color:#e6edf3;
            }
        """)

        root.addWidget(self.plot)
        root.addWidget(self.badge)

    # ==================================================
    # PUBLIC API
    # ==================================================
    def set_model_info(self, name, model_type, lower, upper):
        self.model_name = name
        self.model_type = model_type
        self.lower_limit = lower
        self.upper_limit = upper
        self._update_badge()

    def append_value(self, value: float):
        self.data.append((time.time(), float(value)))
        self._trim_data()
        self._schedule_update()

    def update_cycle_result(self, cycle: dict):
        """
        One annotation per cycle.
        Big, bold, left-aligned text placed on waveform.
        """

        ts = time.time()
        depth = cycle["weld_depth"]
        status = cycle["pass_fail"]

        text_color = "#22c55e" if status == "PASS" else "#ef4444"

        label = pg.TextItem(
            html=(
                "<div style='text-align:left; padding-left:6px;'>"
                f"<span style='font-size:34px; font-weight:900; color:{text_color};'>"
                f"{status}</span><br>"
                f"<span style='font-size:26px; font-weight:700; color:#e6edf3;'>"
                f"{depth:.2f} mm</span>"
                "</div>"
            ),
            anchor=(0, 0)  # left aligned
        )

        label.setZValue(50)
        self.plot.addItem(label)

        self._cycle_overlays.append({
            "ts": ts,
            "label": label
        })

        # Keep display clean
        if len(self._cycle_overlays) > self.MAX_CYCLE_OVERLAYS:
            old = self._cycle_overlays.pop(0)
            self.plot.removeItem(old["label"])

    def reset(self):
        self.data.clear()
        self.curve.clear()
        self._clear_overlays()
        self._update_badge()

    # ==================================================
    # INTERNALS
    # ==================================================
    def _clear_overlays(self):
        for c in self._cycle_overlays:
            self.plot.removeItem(c["label"])
        self._cycle_overlays.clear()


    def _update_plot(self):
        if not self.data:
            return

        times, values = zip(*self.data)
        t0 = times[-1]
        x = [t - t0 for t in times]

        if HAS_NUMPY:
            x = np.asarray(x)
            values = np.asarray(values)

        self.curve.setData(x, values)
        self.plot.setXRange(-self.TIME_WINDOW_SEC, 0)

        ymin, ymax = min(values), max(values)
        pad = max((ymax - ymin) * 0.3, 1.0)
        self.plot.setYRange(ymin - pad, ymax + pad)

        # Move overlays with time
        for c in self._cycle_overlays:
            dx = c["ts"] - t0

            # Slightly below top of waveform
            y_pos = ymax - (ymax - ymin) * 0.15

            c["label"].setPos(dx + 0.2, y_pos)


    def _update_badge(self):
        if not self.model_name:
            self.badge.setText("")
            return

        self.badge.setText(
            f"{self.model_name}  |  {self.model_type}  |  "
            f"Weld Depth Limits: {self.lower_limit:.1f} – {self.upper_limit:.1f} mm"
        )

    def _trim_data(self):
        cutoff = time.time() - self.TIME_WINDOW_SEC
        self.data = [d for d in self.data if d[0] >= cutoff]
        if len(self.data) > self.MAX_POINTS:
            self.data = self.data[-self.MAX_POINTS:]

    def _schedule_update(self):
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(self.UPDATE_INTERVAL_MS)

    def _apply_update(self):
        self._pending_update = False
        self._update_plot()

    # ==================================================
    # WATERMARK
    # ==================================================
    def _install_watermark(self, image_path, opacity, scale_ratio):
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return

        view = self.plot.getViewBox()
        wm = QGraphicsPixmapItem()
        wm.setOpacity(opacity)
        wm.setZValue(-1000)
        view.scene().addItem(wm)

        def update():
            rect = view.sceneBoundingRect()
            w = rect.width() * scale_ratio
            scaled = pixmap.scaledToWidth(int(w), Qt.SmoothTransformation)
            wm.setPixmap(scaled)
            wm.setPos(
                rect.center().x() - scaled.width() / 2,
                rect.center().y() - scaled.height() / 2
            )

        update()
        view.sigResized.connect(update)

    def reset_cycle_markers(self):
        """
        Backward-compatible API.
        Clears all cycle annotations from the plot.
        """
        self._clear_overlays()

