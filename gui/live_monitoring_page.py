# gui/pages/live_monitoring_page.py
import os
import numpy as np
from collections import deque
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, QFile
from PySide6.QtUiTools import QUiLoader
import pyqtgraph as pg


class LiveMonitoringPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.lower_limit = None
        self.upper_limit = None
        self.values = deque(maxlen=400)

        self._load_ui()
        self._setup_plot()
        self._start_render_timer()

    def _load_ui(self):
        ui_path = os.path.join(os.path.dirname(__file__), "ui", "live_monitoring_page.ui")
        if not os.path.exists(ui_path):
            raise FileNotFoundError(f"UI file not found: {ui_path}")

        file = QFile(ui_path)
        if not file.open(QFile.ReadOnly):
            raise RuntimeError(f"Cannot open UI file: {ui_path}")

        loader = QUiLoader()
        self.ui = loader.load(file, self)
        file.close()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ui)

        # Fixed: Use QLabel, not QWidget
        self.model_label    = self.ui.findChild(QLabel, "model_label") or QLabel("Model: -")
        self.limit_label    = self.ui.findChild(QLabel, "limit_label") or QLabel("Limits: -")
        self.value_label    = self.ui.findChild(QLabel, "value_label") or QLabel("Live: -.--- mm")
        self.passfail_label = self.ui.findChild(QLabel, "passfail_label") or QLabel("Status: -")
        self.plot_container = self.ui.findChild(QWidget, "plot_container")

        if not self.plot_container:
            raise RuntimeError("plot_container not found in live_monitoring_page.ui")

    def _setup_plot(self):
        if self.plot_container.layout() is None:
            self.plot_container.setLayout(QVBoxLayout())
            self.plot_container.layout().setContentsMargins(0, 0, 0, 0)

        self.plot = pg.PlotWidget()
        self.plot.setBackground("w")
        self.plot.showGrid(x=True, y=True, alpha=0.7)
        self.plot.setLabel("left", "Height", units="mm")
        self.plot.setLabel("bottom", "Samples")
        self.plot.setTitle("Real-Time Laser Monitoring")

        self.plot_container.layout().addWidget(self.plot)

        self.curve = self.plot.plot(pen=pg.mkPen("#3b82f6", width=2.5))
        self.peak_dot = self.plot.plot(symbol="o", symbolSize=12, symbolBrush="#ef4444")

        self.lower_line = pg.InfiniteLine(angle=0, pen=pg.mkPen("#f97316", width=2, dash=[4,4]))
        self.upper_line = pg.InfiniteLine(angle=0, pen=pg.mkPen("#f97316", width=2, dash=[4,4]))
        self.plot.addItem(self.lower_line)
        self.plot.addItem(self.upper_line)

        self.pass_band = pg.LinearRegionItem(brush=pg.mkBrush(100, 255, 100, 40), movable=False)
        self.plot.addItem(self.pass_band)

    def _start_render_timer(self):
        self.render_timer = QTimer(self)
        self.render_timer.timeout.connect(self._render)
        self.render_timer.start(16)

    def update_graph(self, value: float):
        self.values.append(value)
        self.value_label.setText(f"Live: {value:.3f} mm")

        if self.lower_limit is not None and self.upper_limit is not None:
            in_range = self.lower_limit <= value <= self.upper_limit
            status = "PASS" if in_range else "FAIL"
            color = "#10b981" if in_range else "#ef4444"
            self.passfail_label.setText(f"Status: {status}")
            self.passfail_label.setStyleSheet(f"color: {color}; font-weight: bold;")

    def update_model_info(self, model_name: str, lower: float, upper: float):
        self.lower_limit = lower
        self.upper_limit = upper
        self.model_label.setText(f"Model: {model_name}")
        self.limit_label.setText(f"Limits: {lower:.2f} – {upper:.2f} mm")
        self.lower_line.setValue(lower)
        self.upper_line.setValue(upper)
        self.pass_band.setRegion((lower, upper))

    def _render(self):
        if len(self.values) < 2:
            return
        data = np.array(self.values)
        x = np.arange(len(data))
        self.curve.setData(x, data)

        padding = max(1.0, (data.max() - data.min()) * 0.1)
        self.plot.setYRange(data.min() - padding, data.max() + padding)

        recent = data[-100:]
        if len(recent) > 10:
            peak_offset = len(data) - len(recent)
            peak_idx = np.argmax(recent) + peak_offset
            self.peak_dot.setData([peak_idx], [data[peak_idx]])