# gui/main_window.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, QDateTime, Slot

from backend.models_dao import get_active_model
from backend.cycles_dao import get_cycles
from backend.sms_sender import sms_signals
from gui.windows.settings_window import SettingsWindow

from gui.widgets.plot_panel import PlotPanel
from gui.widgets.result_panel import ResultPanel
from gui.widgets.cycles_panel import CyclesPanel
from gui.widgets.footer_widget import FooterWidget
from gui.widgets.header_widget import HeaderWidget


class MainWindow(QWidget):
    """
    Final MainWindow – Clean Industrial Design
    - Model bar removed
    - Active model displayed only in PlotPanel (as intended)
    - Footer made taller and more prominent using reclaimed space
    """

    def __init__(self, signals):
        super().__init__()
        self.signals = signals

        self.setWindowTitle(
            "NTF Advanced Composites & Engineering Plastics - Pneumatic Laser QC System"
        )
        self.setMinimumSize(1920, 1080)

        self._build_ui()
        self._connect_signals()

        self.showMaximized()

        # Live clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_datetime)
        self.timer.start(1000)
        self._update_datetime()

        QTimer.singleShot(300, self.refresh_active_model)
        QTimer.singleShot(500, self.refresh_cycles)

    # -------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(14)

        # Header
        self.header = HeaderWidget(self.open_settings)
        root.addWidget(self.header)

        # Main content: Plot + Result (left) + Cycles (right)
                # Main content: Plot + Result (left) + Cycles (right)
        content = QHBoxLayout()
        content.setSpacing(14)

        left_column = QVBoxLayout()
        left_column.setSpacing(12)

        self.plot_panel = PlotPanel()
        self.result_panel = ResultPanel()

        left_column.addWidget(self.plot_panel, stretch=2)
        left_column.addWidget(self.result_panel, stretch=1)

        content.addLayout(left_column, stretch=3)

        # Fixed: No walrus operator here
        self.cycles_panel = CyclesPanel()
        content.addWidget(self.cycles_panel, stretch=1)

        root.addLayout(content, stretch=1)

        # Enhanced Footer - now taller using the space freed from model bar
        self.footer = FooterWidget()
        self.footer.setFixedHeight(68)  # Significantly taller for better visibility
        self.footer.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1724, stop:1 #0a101a);
                border-top: 2px solid #1a3a5a;
                border-radius: 0px;
            }
        """)
        root.addWidget(self.footer)

    # -------------------------------------------------
    def _connect_signals(self):
        self.signals.laser_value.connect(self.plot_panel.append_value)
        self.signals.cycle_detected.connect(self.on_cycle_detected)
        self.signals.plc_status.connect(self.footer.update_plc_status)
        self.signals.laser_status.connect(self.on_laser_status)

        sms_signals.sms_sent.connect(self.footer.show_sms)
        sms_signals.modem_status.connect(self.footer.update_modem_status)

    # -------------------------------------------------
    def _update_datetime(self):
        self.header.set_datetime(
            QDateTime.currentDateTime().toString("dddd, dd MMM yyyy | hh:mm:ss")
        )

    def open_settings(self):
        dlg = SettingsWindow(self)
        dlg.settings_applied.connect(self.refresh_active_model)
        dlg.exec()

    def refresh_active_model(self):
        model = get_active_model()
        if not model:
            self.plot_panel.reset()
            return

        name = model["name"]
        model_type = model.get("model_type", "N/A")  # 👈 SAFE DEFAULT
        lo = float(model["lower_limit"])
        hi = float(model["upper_limit"])

        self.plot_panel.configure_limits(lo, hi)
        self.plot_panel.set_model_info(name, model_type, lo, hi)


    @Slot(dict)
    def on_cycle_detected(self, cycle: dict):
        if not cycle.get("completed", True):
            return
        self.result_panel.update_result(cycle)
        QTimer.singleShot(100, self.refresh_cycles)

    def refresh_cycles(self):
        try:
            cycles = get_cycles(limit=40)
        except Exception:
            cycles = []
        self.cycles_panel.update_cycles(cycles)

    @Slot(str)
    def on_laser_status(self, status: str):
        self.footer.update_laser_status(status)
        if status != "CONNECTED":
            self.plot_panel.show_no_data()
            self.result_panel.show_error("LASER DISCONNECTED")