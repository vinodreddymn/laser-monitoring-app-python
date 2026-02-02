# gui/widgets/plot_panel.py

import time
import logging
from typing import List, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

import pyqtgraph as pg
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QGraphicsPixmapItem
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap

log = logging.getLogger(__name__)


class PlotPanel(QFrame):
    """
    Industrial Welding Laser Plot (Clarity-First)

    ✔ Raw laser waveform
    ✔ Touch-point reference line
    ✔ Live laser value badge
    ✔ PASS / FAIL cycle annotations
    ✔ Branding watermark
    """

    TIME_WINDOW_SEC = 60
    MAX_POINTS = 900
    UPDATE_INTERVAL_MS = 100
    MAX_CYCLE_OVERLAYS = 6

    # --------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        # ---------------- Live Data ----------------
        self.data: List[Tuple[float, float]] = []
        self.latest_value: float | None = None

        # ---------------- Model Info ----------------
        self.model_name = ""
        self.model_type = ""
        self.lower_limit = 0.0
        self.upper_limit = 0.0
        self.touch_point: float | None = None

        # ---------------- Touch Point Line ----------------
        self._touch_line: pg.InfiniteLine | None = None

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
        self.badge.setFont(QFont("Segoe UI", 18, QFont.Bold))
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
    def set_model_info(self, name, model_type, lower, upper, touch_point):
        self.model_name = name
        self.model_type = model_type
        self.lower_limit = lower
        self.upper_limit = upper
        self.touch_point = touch_point

        self._install_touch_line()
        self._update_badge()

    def append_value(self, value: float):
        self.latest_value = float(value)
        self.data.append((time.time(), self.latest_value))
        self._trim_data()
        self._schedule_update()

    def reset(self):
        self.data.clear()
        self.latest_value = None
        self.curve.clear()
        self._clear_overlays()
        self._remove_touch_line()
        self._update_badge()

    def show_no_data(self):
        self.curve.clear()
        self.badge.setText("NO DATA")

    # ==================================================
    # TOUCH POINT LINE
    # ==================================================
    def _install_touch_line(self):
        self._remove_touch_line()

        if self.touch_point is None:
            return

        self._touch_line = pg.InfiniteLine(
            pos=self.touch_point,
            angle=0,
            pen=pg.mkPen("#f59e0b", width=2, style=Qt.DashLine)
        )
        self._touch_line.setZValue(20)
        self.plot.addItem(self._touch_line)

    def _remove_touch_line(self):
        if self._touch_line:
            self.plot.removeItem(self._touch_line)
            self._touch_line = None

    # ==================================================
    # CYCLE ANNOTATION (CALLED BY MainWindow)
    # ==================================================
    def update_cycle_result(self, cycle: dict):
        """
        Annotate completed cycle on the plot.
        """
        try:
            ts = time.time()

            result = cycle.get("pass_fail", "UNKNOWN")
            weld_depth = float(cycle.get("weld_depth", 0.0))

            color = "#00ffaa" if result == "PASS" else "#ff4444"

            label = pg.TextItem(
                html=(
                    f"<div style='text-align:center;'>"
                    f"<span style='font-size:22px; font-weight:bold; color:{color};'>"
                    f"{result}</span><br>"
                    f"<span style='font-size:18px; color:#e6edf3;'>"
                    f"{weld_depth:.2f} mm</span>"
                    f"</div>"
                ),
                anchor=(0.5, 1.0)
            )

            label.setZValue(30)
            self.plot.addItem(label)

            self._cycle_overlays.append({
                "ts": ts,
                "label": label,
            })

            if len(self._cycle_overlays) > self.MAX_CYCLE_OVERLAYS:
                old = self._cycle_overlays.pop(0)
                self.plot.removeItem(old["label"])

        except Exception:
            log.exception("Failed to update cycle overlay")

    # ==================================================
    # INTERNALS
    # ==================================================
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

        if self.touch_point is not None:
            ymin = min(ymin, self.touch_point)
            ymax = max(ymax, self.touch_point)

        self.plot.setYRange(ymin - pad, ymax + pad)

        for c in self._cycle_overlays:
            dx = c["ts"] - t0
            y_pos = ymax - (ymax - ymin) * 0.15
            c["label"].setPos(dx + 0.2, y_pos)

        self._update_badge()

    def _update_badge(self):
        if not self.model_name:
            self.badge.setText("")
            return

        live = (
            f"{self.latest_value:.2f} mm"
            if self.latest_value is not None else "—"
        )

        self.badge.setText(
            f"{self.model_name} | {self.model_type} | "
            f"Limits: {self.lower_limit:.1f} – {self.upper_limit:.1f} mm | "
            f"Touch: {self.touch_point:.2f} mm | "
            f"Live: {live}"
        )

    def _clear_overlays(self):
        for c in self._cycle_overlays:
            self.plot.removeItem(c["label"])
        self._cycle_overlays.clear()

    def reset_cycle_markers(self):
        self._clear_overlays()

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
