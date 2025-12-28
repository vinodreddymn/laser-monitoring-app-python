# gui/main_window.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog
)
from PySide6.QtCore import Qt, QTimer, QDateTime, Slot

from backend.models_dao import get_active_model
from backend.cycles_dao import get_cycles
from backend.sms_sender import sms_signals
from backend.gsm_modem import modem_signals
from backend.usb_printer_manager import printer_signals

from gui.windows.settings_window import SettingsWindow
from gui.windows.password_modal import PasswordModal
from gui.widgets.plot_panel import PlotPanel
from gui.widgets.result_panel import ResultPanel
from gui.widgets.cycles_panel import CyclesPanel
from gui.widgets.footer_widget import FooterWidget
from gui.widgets.header_widget import HeaderWidget


class MainWindow(QWidget):
    """
    Main Application Window – Production Tight Layout

    Principles:
    - Zero wasted space
    - Header/Footer fixed (60 px)
    - Plot dominates
    - Result compact
    - Cycles aligned, no float gaps
    """


    KIOSK_MODE = True

    def __init__(self, signals):
        super().__init__()
        self.signals = signals

        self.setWindowTitle(
            "NTF Advanced Composites & Engineering Plastics – Pneumatic Laser QC System"
        )
        self.setMinimumSize(1600, 900)

        self._build_ui()
        self._connect_signals()
        self._init_timers()

        if self.KIOSK_MODE:
            self.setWindowFlags(
                Qt.FramelessWindowHint |
                Qt.WindowStaysOnTopHint
            )
            self.showFullScreen()
        else:
            self.showMaximized()


        QTimer.singleShot(300, self.refresh_active_model)
        QTimer.singleShot(500, self.refresh_cycles)

    # ============================================================
    # UI
    # ============================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(6, 6, 6, 6)   # 🔽 drastically reduced
        root.setSpacing(6)

        # ---------------- HEADER ----------------
        self.header = HeaderWidget(self.open_settings)
        root.addWidget(self.header)

        # ---------------- MAIN CONTENT ----------------
        content = QHBoxLayout()
        content.setSpacing(6)
        content.setContentsMargins(0, 0, 0, 0)

        # ===== LEFT: Plot + Result =====
        left = QVBoxLayout()
        left.setSpacing(6)
        left.setContentsMargins(0, 0, 0, 0)

        self.plot_panel = PlotPanel()
        self.result_panel = ResultPanel()

        left.addWidget(self.plot_panel, stretch=7)
        left.addWidget(self.result_panel, stretch=3)

        # ===== RIGHT: Cycles =====
        self.cycles_panel = CyclesPanel(kiosk_mode=self.KIOSK_MODE)


        content.addLayout(left, stretch=4)
        content.addWidget(self.cycles_panel, stretch=1)

        root.addLayout(content, stretch=1)

        # ---------------- FOOTER ----------------
        self.footer = FooterWidget()
        root.addWidget(self.footer)

    # ============================================================
    # SIGNALS
    # ============================================================
    def _connect_signals(self):
        # Laser values
        self.signals.laser_value.connect(self.plot_panel.append_value)

        # Cycle detection
        self.signals.cycle_detected.connect(self.on_cycle_detected)

        # Laser connection state (UI only)
        self.signals.laser_status.connect(self.on_laser_status)

        # PLC
        self.signals.plc_status.connect(self.footer.update_plc_status)

        # GSM modem
        modem_signals.modem_connected.connect(
            self.footer.update_modem_status
        )

        # Printer
        printer_signals.printer_status.connect(
            self.footer.update_printer_status
        )

        # SMS
        sms_signals.sms_sent.connect(self.footer.show_sms)

    # ============================================================
    # TIMERS
    # ============================================================
    def _init_timers(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_datetime)
        self.clock_timer.start(1000)
        self._update_datetime()

    # ============================================================
    # HEADER
    # ============================================================
    def _update_datetime(self):
        self.header.set_datetime(
            QDateTime.currentDateTime().toString(
                "dddd, dd MMM yyyy | HH:mm:ss"
            )
        )

    # ============================================================
    # SETTINGS
    # ============================================================
    def open_settings(self):
        password_modal = PasswordModal(self)
        if password_modal.exec() != QDialog.Accepted:
            return

        dlg = SettingsWindow(self)
        dlg.settings_applied.connect(self.refresh_active_model)
        dlg.exec()

    # ============================================================
    # MODEL
    # ============================================================
    def refresh_active_model(self):
        model = get_active_model()
        if not model:
            self.plot_panel.reset()
            return

        name = model["name"]
        model_type = model.get("model_type", "N/A")
        lower = float(model["lower_limit"])
        upper = float(model["upper_limit"])

        self.plot_panel.configure_limits(lower, upper)
        self.plot_panel.set_model_info(
            name, model_type, lower, upper
        )

    # ============================================================
    # CYCLES
    # ============================================================
    @Slot(dict)
    def on_cycle_detected(self, cycle: dict):
        if not cycle.get("completed", True):
            return

        self.result_panel.update_result(cycle)
        QTimer.singleShot(80, self.refresh_cycles)

    def refresh_cycles(self):
        try:
            cycles = get_cycles(limit=40)
        except Exception:
            cycles = []

        self.cycles_panel.update_cycles(cycles)

    # ============================================================
    # LASER STATUS (UI ONLY)
    # ============================================================
    @Slot(str)
    def on_laser_status(self, status: str):
        if status != "CONNECTED":
            self.plot_panel.show_no_data()
            self.result_panel.show_error("NO DATA")
