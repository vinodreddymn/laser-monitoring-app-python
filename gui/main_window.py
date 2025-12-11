import os
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGridLayout, QStyle
)
from PySide6.QtCore import Qt, Slot, QTimer, QDateTime
from PySide6.QtGui import QFont, QIcon

import pyqtgraph as pg

from backend.models_dao import get_active_model
from backend.cycles_dao import get_cycles
from backend.sms_sender import sms_signals
from gui.windows.settings_window import SettingsWindow


class MainWindow(QWidget):
    def __init__(self, signals):
        super().__init__()
        self.signals = signals

        self.max_points = 800
        self.laser_history = []

        self.setWindowTitle("NTF Advanced Composites & Engineering Plastics - Pneumatic Laser QC System")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 900)

        self.init_ui()
        self.connect_signals()

        # Live Clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()

        # Auto-hide SMS footer
        self.sms_hide_timer = QTimer(self)
        self.sms_hide_timer.setSingleShot(True)
        self.sms_hide_timer.timeout.connect(self.clear_sms_footer)

        # Initial load
        QTimer.singleShot(300, self.refresh_active_model)
        QTimer.singleShot(500, self.refresh_cycle_list)

    # ===================== UI SETUP =====================
    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        # --------------------- TOP BAR ---------------------
        top_bar = QHBoxLayout()
        logo_label = QLabel()
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            logo_label.setPixmap(QIcon(logo_path).pixmap(64, 64))

        company = QLabel("NTF ADVANCED COMPOSITES & ENGINEERING PLASTICS")
        company.setFont(QFont("Segoe UI", 18, QFont.Bold))
        company.setStyleSheet("color: #00aaff;")

        self.datetime_label = QLabel()
        self.datetime_label.setFont(QFont("Segoe UI", 12))
        self.datetime_label.setStyleSheet("color: #88ccff;")

        settings_btn = QPushButton("Settings")
        settings_btn.setFixedSize(120, 36)
        settings_btn.setIcon(QIcon.fromTheme("preferences-system"))
        if settings_btn.icon().isNull():
            settings_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        settings_btn.clicked.connect(self.open_settings)

        top_bar.addWidget(logo_label)
        top_bar.addWidget(company)
        top_bar.addStretch()
        top_bar.addWidget(self.datetime_label)
        top_bar.addSpacing(18)
        top_bar.addWidget(settings_btn)
        root.addLayout(top_bar)

        # --------------------- MODEL BAR ---------------------
        self.model_bar = QFrame()
        self.model_bar.setObjectName("modelBar")
        self.model_bar.setStyleSheet("""
            #modelBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0a1a2a, stop:1 #001122);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        model_layout = QHBoxLayout(self.model_bar)
        model_layout.setContentsMargins(8, 8, 8, 8)

        self.model_info_label = QLabel("No Active Model")
        self.model_info_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.model_info_label.setStyleSheet("color: #88ff88;")

        model_layout.addWidget(QLabel("Active Model:"))
        model_layout.addWidget(self.model_info_label)
        model_layout.addStretch()
        root.addWidget(self.model_bar)

        # --------------------- MAIN CONTENT ---------------------
        content = QHBoxLayout()
        content.setSpacing(12)

        # LEFT: Graph + Result Panel
        left_col = QVBoxLayout()
        left_col.setSpacing(8)

        # Graph
        self.plot_widget = pg.PlotWidget(background="#0a0f1a")
        self.plot_widget.setLabel("left", "Height (mm)")
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.curve = self.plot_widget.plot(pen=pg.mkPen("#00ff99", width=3))
        self.baseline = self.plot_widget.plot(pen=None)
        self.fill = pg.FillBetweenItem(self.curve, self.baseline, brush=pg.mkBrush(0, 255, 153, 70))
        self.plot_widget.addItem(self.fill)
        self.upper_line = self.plot_widget.addLine(y=10.0, pen=pg.mkPen("#ff4444", width=3, style=Qt.DashLine))
        self.lower_line = None
        left_col.addWidget(self.plot_widget, stretch=2)

        # Result panel
        result_frame = QFrame()
        result_frame.setStyleSheet("background: #111; border-radius: 8px; padding: 10px;")
        result_layout = QGridLayout(result_frame)
        result_layout.setContentsMargins(10, 10, 10, 10)
        result_layout.setHorizontalSpacing(12)
        result_layout.setVerticalSpacing(8)

        self.status_label = QLabel("Waiting for cycle...")
        self.status_label.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888;")

        self.details_label = QLabel("")
        self.details_label.setFont(QFont("Segoe UI", 12))
        self.details_label.setWordWrap(True)
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("color: #ddd;")

        self.qr_code_label = QLabel("—")
        self.qr_code_label.setAlignment(Qt.AlignCenter)
        self.qr_code_label.setStyleSheet("""
            color: #00ff88;
            background: #000;
            border: 2px solid #333;
            border-radius: 8px;
            padding: 10px;
        """)
        self.qr_code_label.setFont(QFont("Segoe UI", 28, QFont.Bold))
        self.qr_code_label.setWordWrap(True)
        self.qr_code_label.setFixedHeight(160)

        result_layout.addWidget(self.status_label, 0, 0, 1, 2)
        result_layout.addWidget(self.details_label, 1, 0, 1, 2)
        result_layout.addWidget(self.qr_code_label, 0, 2, 2, 1)

        left_col.addWidget(result_frame, stretch=1)
        content.addLayout(left_col, stretch=3)

        # RIGHT: Latest Cycles Panel (new design)
        right_col = QVBoxLayout()
        right_col.setSpacing(8)

        cycles_panel = QFrame()
        cycles_panel.setStyleSheet("""
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 12px;
        """)
        cycles_layout = QVBoxLayout(cycles_panel)
        cycles_layout.setContentsMargins(14, 12, 14, 12)
        cycles_layout.setSpacing(8)

        title = QLabel("Latest Cycles")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #58a6ff;")
        cycles_layout.addWidget(title)

        # Container for cards
        self.cycles_container = QVBoxLayout()
        self.cycles_container.setSpacing(7)
        self.cycles_container.setContentsMargins(0, 0, 0, 0)

        container_widget = QWidget()
        container_widget.setLayout(self.cycles_container)
        cycles_layout.addWidget(container_widget)

        right_col.addWidget(cycles_panel)
        content.addLayout(right_col, stretch=1)

        root.addLayout(content)

        # --------------------- FOOTER ---------------------
        footer = QFrame()
        footer.setStyleSheet("background: #0a0f1a; border-top: 1px solid #222; padding: 8px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(8, 4, 8, 4)

        self.sms_engine_label = QLabel("SMS: RUNNING")
        self.plc_status_label = QLabel("PLC: ---")
        self.laser_status_label = QLabel("Laser: ---")

        for lbl in (self.sms_engine_label, self.plc_status_label, self.laser_status_label):
            lbl.setFont(QFont("Segoe UI", 11))
            lbl.setStyleSheet("color: #ccc;")

        self.footer_label = QLabel("System Ready")
        self.footer_label.setFont(QFont("Segoe UI", 11))
        self.footer_label.setStyleSheet("color: #666;")

        footer_layout.addWidget(self.sms_engine_label)
        footer_layout.addSpacing(18)
        footer_layout.addWidget(self.plc_status_label)
        footer_layout.addSpacing(18)
        footer_layout.addWidget(self.laser_status_label)
        footer_layout.addStretch()
        footer_layout.addWidget(self.footer_label)

        root.addWidget(footer)

    # ===================== SIGNALS =====================
    def connect_signals(self):
        self.signals.laser_value.connect(self.update_laser_value)
        self.signals.cycle_detected.connect(self.on_cycle_detected)
        self.signals.plc_status.connect(self.update_plc_status)
        self.signals.laser_status.connect(self.update_laser_status)
        sms_signals.sms_sent.connect(self.update_sms_sent)
        sms_signals.sms_engine.connect(self.update_sms_engine)

    # ===================== CLOCK =====================
    def update_datetime(self):
        now = QDateTime.currentDateTime().toString("dddd, dd MMM yyyy | hh:mm:ss")
        self.datetime_label.setText(now)

    # ===================== SETTINGS =====================
    def open_settings(self):
        dialog = SettingsWindow(self)
        dialog.settings_applied.connect(self.on_settings_applied)
        dialog.exec()

    @Slot(dict)
    def on_settings_applied(self, payload: dict):
        if payload.get("model_id"):
            self.refresh_active_model()

    # ===================== MODEL =====================
    def refresh_active_model(self):
        model = get_active_model()
        if not model:
            self.model_info_label.setText("No Active Model")
            return

        name = model["name"]
        lower = model["lower_limit"]
        upper = model["upper_limit"]
        self.model_info_label.setText(f"{name} | Range: {lower:.1f} – {upper:.1f} mm")
        self.plot_widget.setYRange(0, max(upper * 1.5, 10))
        self.upper_line.setValue(upper)
        if self.lower_line:
            self.plot_widget.removeItem(self.lower_line)
        self.lower_line = self.plot_widget.addLine(y=lower, pen=pg.mkPen("#4488ff", width=3, style=Qt.DashLine))

    # ===================== DATA UPDATES =====================
    @Slot(float)
    def update_laser_value(self, value: float):
        self.laser_history.append(value)
        if len(self.laser_history) > self.max_points:
            self.laser_history.pop(0)
        x = list(range(len(self.laser_history)))
        self.curve.setData(x, self.laser_history)
        self.baseline.setData(x, [0] * len(x))
        self.plot_widget.setXRange(max(0, len(x) - 150), len(x))

    # ===================== CYCLE RESULT =====================
    @Slot(dict)
    def on_cycle_detected(self, cycle: dict):
        status = cycle.get("pass_fail", "UNKNOWN")
        peak = cycle.get("peak_height", 0.0)
        model_name = cycle.get("model_name", "Unknown")
        timestamp = cycle.get("timestamp", datetime.now().isoformat())
        qr_code = cycle.get("qr_text") or cycle.get("qr_code") or ""

        # Normalise timestamp
        if isinstance(timestamp, datetime):
            dt = timestamp
        else:
            try:
                dt = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            except:
                dt = datetime.now()

        time_str = dt.strftime("%d %b %Y, %H:%M:%S")

        if status == "PASS":
            self.status_label.setText("PASS")
            self.status_label.setStyleSheet("color: #00ff88; font-size: 32px;")
            self.details_label.setText(f"Model: {model_name}\nPeak: {peak:.2f} mm\nTime: {time_str}")
            self.qr_code_label.setText(qr_code if qr_code else "—")
        else:
            self.status_label.setText("FAIL")
            self.status_label.setStyleSheet("color: #ff4444; font-size: 32px;")
            self.details_label.setText(f"Failed | Peak: {peak:.2f} mm | {time_str}")
            self.qr_code_label.setText("—")

        QTimer.singleShot(100, self.refresh_cycle_list)

    # ===================== LATEST CYCLES PANEL =====================
    def create_cycle_card(self, cycle: dict) -> QWidget:
        card = QFrame()
        card.setFixedHeight(74)
        card.setStyleSheet("""
            QFrame {
                background: #161b22;
                border-radius: 10px;
                border: 1px solid #30363d;
            }
            QFrame:hover {
                background: #1f252e;
                border: 1px solid #58a6ff;
            }
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        # ---- Status ----
        status = (cycle.get("pass_fail") or "").upper()
        is_pass = status == "PASS"
        status_color = "#39d353" if is_pass else "#f85149"
        status_text = "PASS" if is_pass else "FAIL"

        status_lbl = QLabel(status_text)
        status_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        status_lbl.setStyleSheet(f"color: {status_color};")

        # ---- Model ----
        model = cycle.get("model_name") or "—"
        model_lbl = QLabel(model)
        model_lbl.setFont(QFont("Segoe UI", 11))
        model_lbl.setStyleSheet("color: #c9d1d9;")

        # ---- Timestamp (robust handling) ----
        ts = cycle.get("timestamp")
        if isinstance(ts, datetime):
            dt = ts
        else:
            try:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            except:
                dt = datetime.now()

        time_str = dt.strftime("%H:%M:%S")
        date_str = dt.strftime("%d %b")

        time_lbl = QLabel(time_str)
        time_lbl.setFont(QFont("Segoe UI", 10, QFont.Medium))
        time_lbl.setStyleSheet("color: #8b949e;")

        date_lbl = QLabel(date_str)
        date_lbl.setFont(QFont("Segoe UI", 9))
        date_lbl.setStyleSheet("color: #58a6ff;")

        # ---- QR Code ----
        qr_text = cycle.get("qr_code") or cycle.get("qr_text") or ""
        qr_lbl = QLabel()
        if is_pass and qr_text:
            qr_lbl.setText(qr_text.strip())
            qr_lbl.setFont(QFont("Consolas", 13, QFont.Bold))
            qr_lbl.setStyleSheet("""
                color: #39d353;
                background: #0d1b0d;
                padding: 8px 12px;
                border-radius: 8px;
                border: 1px solid #39d35344;
            """)
            qr_lbl.setAlignment(Qt.AlignCenter)
        else:
            qr_lbl.setText("—")
            qr_lbl.setStyleSheet("color: #666666;")
            qr_lbl.setFont(QFont("Segoe UI", 11))

        # Layout assembly
        left_v = QVBoxLayout()
        left_v.setSpacing(2)
        left_v.addWidget(status_lbl)
        left_v.addWidget(model_lbl)

        time_v = QVBoxLayout()
        time_v.setSpacing(1)
        time_v.addWidget(time_lbl)
        time_v.addWidget(date_lbl)
        time_v.addStretch()

        layout.addLayout(left_v, stretch=2)
        layout.addLayout(time_v, stretch=1)
        layout.addWidget(qr_lbl, stretch=3)

        return card

    def refresh_cycle_list(self):
        # Clear
        while self.cycles_container.count():
            item = self.cycles_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            cycles = get_cycles(limit=20)
        except Exception as e:
            cycles = []
            print("DB error:", e)

        if not cycles:
            lbl = QLabel("No cycles recorded yet")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #666; font-style: italic; padding: 30px;")
            self.cycles_container.addWidget(lbl)
            return

        # Newest on top
        cycles = cycles[::-1]

        # Rough height calculation – works perfectly on all screen sizes
        approx_height = self.height() - 320
        max_cards = max(4, approx_height // 82)

        for cycle in cycles[:max_cards]:
            card = self.create_cycle_card(cycle)
            self.cycles_container.addWidget(card)

        self.cycles_container.addStretch()

    # ===================== FOOTER STATUS =====================
    @Slot(dict)
    def update_plc_status(self, status: dict):
        state = status.get("state", "UNKNOWN")
        color = "#00ff88" if state == "CONNECTED" else "#ff4444"
        self.plc_status_label.setText(f"PLC: {state}")
        self.plc_status_label.setStyleSheet(f"color:{color};")

    @Slot(str)
    def update_laser_status(self, status: str):
        color = "#00ff88" if status == "CONNECTED" else "#ff4444"
        self.laser_status_label.setText(f"Laser: {status}")
        self.laser_status_label.setStyleSheet(f"color:{color};")

    @Slot(dict)
    def update_sms_sent(self, info: dict):
        phone = info.get("phone", "---")
        time_str = info.get("time", "---")
        message = info.get("message", "Sent")
        self.footer_label.setText(f"SMS → {phone} at {time_str} | {message}")
        self.footer_label.setStyleSheet("color:#00ff88; font-weight:bold;")
        self.sms_hide_timer.start(3000)

    @Slot(bool)
    def update_sms_engine(self, running: bool):
        if running:
            self.sms_engine_label.setText("SMS: RUNNING")
            self.sms_engine_label.setStyleSheet("color:#00ff88;")
        else:
            self.sms_engine_label.setText("SMS: STOPPED")
            self.sms_engine_label.setStyleSheet("color:#ff4444;")

    def clear_sms_footer(self):
        self.footer_label.setText("System Ready")
        self.footer_label.setStyleSheet("color:#666;")