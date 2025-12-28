import time
import logging
from typing import Optional, List, Tuple

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("NumPy not available; using list-based plotting.")

import pyqtgraph as pg
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsPixmapItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPixmap

log = logging.getLogger(__name__)


class PlotPanel(QFrame):
    """
    Laser Plot Panel (display-only)

    Features:
    - Time-based X axis (labels hidden)
    - Auto-fit Y to data + tolerance
    - Static watermark filling entire plot panel
    - Model badge (Model | Current | Min | Max)
    - NO DATA overlay
    - Throttled updates (~10 FPS)
    """

    MAX_POINTS = 800
    TIME_WINDOW_SEC = 60
    UPDATE_INTERVAL_MS = 100     # ~10 FPS
    DOWNSAMPLE_TO = 400

    # ------------------------------------------------------------------
    # Init
    # ------------------------------------------------------------------
    def __init__(
        self,
        parent=None,
        max_points: int = MAX_POINTS,
        time_window_sec: int = TIME_WINDOW_SEC
    ):
        super().__init__(parent)

        self.max_points = max_points
        self.time_window_sec = time_window_sec

        # Data
        self.data: List[Tuple[float, float]] = []
        self.lower: Optional[float] = None
        self.upper: Optional[float] = None
        self.model_name: str = ""
        self.model_type: str = ""

        self.current_value: Optional[float] = None

        # Plot items
        self._lower_line = None
        self._upper_line = None
        self._watermark_item: Optional[QGraphicsPixmapItem] = None

        # Update throttling
        self._pending_update = False
        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._apply_update)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0a0f1a, stop:1 #0d1117);
                border-radius: 8px;
                border: 1px solid #30363d;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(4)

        # ---------------- Plot ----------------
        self.plot = pg.PlotWidget(background="#0a0f1a")
        self.plot.showGrid(x=True, y=True, alpha=0.3)
        self.plot.setLabel("left", "Laser Height (mm)")

        y_axis = self.plot.getAxis("left")
        y_axis.setStyle(tickFont=QFont("Segoe UI", 11))
        y_axis.label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        y_axis.setTextPen("#e6edf3")

        self.plot.setLabel("bottom", "")

        self.plot.setMouseEnabled(False, False)
        self.plot.enableAutoRange(False, False)

        # Axis styling
        x_axis = self.plot.getAxis("bottom")
        x_axis.setTicks([])
        x_axis.setPen("#0a0f1a")
        x_axis.setTextPen("#0a0f1a")

        y_axis = self.plot.getAxis("left")
        y_axis.setPen("#30363d")
        y_axis.setTextPen("#e6edf3")

        # Curve
        self.curve = self.plot.plot(
            pen=pg.mkPen("#00ff99", width=3)
        )

        # Watermark (static, panel-filling)
        
        self._install_watermark(
            image_path="assets/watermark.png",
            opacity=0.1,
            scale_ratio=0.80   # try 0.25–0.4
        )

        
        


        # ---------------- Badge ----------------
        self.badge_frame = QFrame()
        self.badge_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1622,
                    stop:1 #0b1220
                );
                border-radius: 8px;
                border: 1px solid #2d3b4f;
            }
            QLabel {
                background: transparent;
                color: #e6edf3;
            }
        """)


        badge_layout = QHBoxLayout(self.badge_frame)
        badge_layout.setContentsMargins(12, 8, 12, 8)
        badge_layout.setSpacing(10)

        self.badge_label = QLabel("")
        self.badge_label.setFont(QFont("Segoe UI", 13))
        self.badge_label.setTextFormat(Qt.RichText)

        badge_layout.addWidget(self.badge_label)
        badge_layout.addStretch()

        # ---------------- NO DATA ----------------
        self.no_data_lbl = QLabel("NO DATA")
        self.no_data_lbl.setAlignment(Qt.AlignCenter)
        self.no_data_lbl.setStyleSheet("""
            color:#ff4444;
            font-size:32px;
            font-weight:bold;
            background:rgba(10,15,26,0.85);
            border-radius:8px;
        """)
        self.no_data_lbl.hide()

        root.addWidget(self.plot)
        root.addWidget(self.badge_frame, alignment=Qt.AlignRight | Qt.AlignTop)
        root.addWidget(self.no_data_lbl, alignment=Qt.AlignCenter)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def configure_limits(self, lower: float, upper: float):
        self.lower = lower
        self.upper = upper
        self._draw_tolerance_lines()
        self.reset()

    def set_model_info(self, name: str, model_type: str, lower: float, upper: float):
        self.model_name = name
        self.model_type = model_type
        self.lower = lower
        self.upper = upper
        self._draw_tolerance_lines()
        self._update_badge()




    def append_value(self, value: float):
        now = time.time()
        self.no_data_lbl.hide()

        self.data.append((now, float(value)))
        self.current_value = float(value)

        self._trim_data()
        self._schedule_update()

    def show_no_data(self):
        self.no_data_lbl.show()
        self._update_badge()

    def reset(self):
        self.data.clear()
        self.curve.clear()
        self.current_value = None
        self._update_badge()
        self.no_data_lbl.hide()

    # ------------------------------------------------------------------
    # Internal logic
    # ------------------------------------------------------------------
    def _draw_tolerance_lines(self):
        if self._lower_line:
            self.plot.removeItem(self._lower_line)
        if self._upper_line:
            self.plot.removeItem(self._upper_line)

        if self.lower is not None:
            self._lower_line = self.plot.addLine(
                y=self.lower,
                pen=pg.mkPen("#4488ff", width=2, style=Qt.DashLine)
            )

        if self.upper is not None:
            self._upper_line = self.plot.addLine(
                y=self.upper,
                pen=pg.mkPen("#ff4444", width=2, style=Qt.DashLine)
            )

    def _trim_data(self):
        cutoff = time.time() - self.time_window_sec
        self.data = [d for d in self.data if d[0] >= cutoff]

        if len(self.data) > self.max_points:
            self.data = self.data[-self.max_points:]

        if len(self.data) > self.DOWNSAMPLE_TO:
            step = max(1, len(self.data) // self.DOWNSAMPLE_TO)
            self.data = self.data[::step]

    def _schedule_update(self):
        if not self._pending_update:
            self._pending_update = True
            self._update_timer.start(self.UPDATE_INTERVAL_MS)

    def _apply_update(self):
        self._pending_update = False
        self._update_plot()
        self._update_badge()

    def _update_plot(self):
        if not self.data:
            return

        times, values = zip(*self.data)
        t_ref = times[-1]

        x = [t - t_ref for t in times]

        if HAS_NUMPY:
            x = np.asarray(x)
            values = np.asarray(values)

        self.curve.setData(x, values)
        self.plot.setXRange(-self.time_window_sec, 0)

        ymin = float(min(values))
        ymax = float(max(values))

        if self.lower is not None and self.upper is not None:
            ymin = min(ymin, self.lower)
            ymax = max(ymax, self.upper)

        pad = max((ymax - ymin) * 0.25, 1.0)
        self.plot.setYRange(ymin - pad, ymax + pad)

    def _update_badge(self):
        if not self.model_name:
            self.badge_label.setText("")
            return

        lower = self.lower if self.lower is not None else 0.0
        upper = self.upper if self.upper is not None else 0.0

        model_html = (
            f"<span style='font-size:24px; font-weight:800; color:#58a6ff;'>"
            f"{self.model_name}</span>"
        )

        type_html = (
            f"<span style='font-size:20px; font-weight:600; color:#ffa657;'>"
            f" &nbsp;[{self.model_type}]</span>"
        )

        limits_html = (
            f"<span style='font-size:18px; color:#9da7b1;'>"
            f" | Min: {lower:.2f} mm"
            f" | Max: {upper:.2f} mm"
            f"</span>"
        )


        if self.current_value is None:
            current_html = (
                f"<span style='font-size:22px; color:#8b949e;'>"
                f" | Current: --</span>"
            )
        else:
            current_html = (
                f"<span style='font-size:24px; font-weight:700; color:#00ff99;'>"
                f" | Current: {self.current_value:.2f} mm</span>"
            )

        self.badge_label.setText(
            model_html + type_html + limits_html + current_html
        )



    # ------------------------------------------------------------------
    # Watermark (static, panel-filling)
    # ------------------------------------------------------------------
            # ------------------------------------------------------------------
    # Watermark (static, centered logo)
    # ------------------------------------------------------------------
    def _install_watermark(
        self,
        image_path: str,
        opacity: float = 0.9,
        scale_ratio: float = 0.35  # 35% of plot width
    ):
            """
            Centered static watermark logo.
            - NOT affected by zoom or graph range
            - Centered in plot panel
            - Scales relative to plot size
            """

            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                log.warning("Watermark image not found: %s", image_path)
                return

            view = self.plot.getViewBox()

            self._watermark_item = QGraphicsPixmapItem()
            self._watermark_item.setOpacity(opacity)
            self._watermark_item.setZValue(-1000)
            view.scene().addItem(self._watermark_item)

            def update_watermark():
                rect = view.sceneBoundingRect()
                target_w = rect.width() * scale_ratio

                scaled = pixmap.scaledToWidth(
                    max(1, int(target_w)),
                    Qt.SmoothTransformation
                )

                self._watermark_item.setPixmap(scaled)

                x = rect.center().x() - scaled.width() / 2
                y = rect.center().y() - scaled.height() / 2
                self._watermark_item.setPos(x, y)

            # Initial placement
            update_watermark()

            # Re-center on resize
            view.sigResized.connect(update_watermark)