from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog, QMessageBox, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QDateTime, Slot
from PySide6.QtGui import QFont

from backend.models_dao import get_active_model
from backend.cycles_dao import get_cycles
from backend.sms_sender import sms_signals
from backend.gsm_modem import modem_signals
from backend.usb_printer_manager import printer_signals


from config.app_config import WINDOW_TITLE

from gui.windows.settings_window import SettingsWindow
from gui.windows.password_modal import PasswordModal
from gui.windows.qr_print_dialog import QRPrintDialog
from gui.widgets.plot_panel import PlotPanel
from gui.widgets.result_panel import ResultPanel
from gui.widgets.cycles_panel import CyclesPanel
from gui.widgets.footer_widget import FooterWidget
from gui.widgets.header_widget import HeaderWidget
from gui.styles.app_styles import apply_base_dialog_style



# ============================================================
# SHUTDOWN CONFIRMATION DIALOG
# ============================================================
class ShutdownConfirmDialog(QDialog):
    """
    Shutdown Confirmation Dialog – Industrial HMI Uniform

    • Consistent with other dialogs
    • Clear warning text
    • Factory-safe styling
    """

    WIDTH = 700
    HEIGHT = 420

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("ShutdownConfirmDialog")
        self.setWindowTitle("Confirm System Shutdown")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()
        apply_base_dialog_style(self)

        # Override fonts for larger text
        self.title.setStyleSheet("font-size: 28pt; font-weight: bold; color: #f8fafc;")
        self.warning.setStyleSheet("font-size: 18pt; color: #94a3b8;")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(22)

        # ---------------- Title ----------------
        self.title = QLabel("Exit Pneumatic Laser QC System?")
        self.title.setObjectName("DialogTitle")
        self.title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title)

        # ---------------- Warning Text ----------------
        self.warning = QLabel(
            "This will safely stop all system services and power down the application.\n\n"
            "Ensure no active welding cycle is in progress."
        )
        self.warning.setObjectName("MutedText")
        self.warning.setAlignment(Qt.AlignCenter)
        self.warning.setWordWrap(True)
        root.addWidget(self.warning)

        root.addStretch()

        # ---------------- Buttons ----------------
        button_row = QHBoxLayout()
        button_row.setSpacing(12)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("role", "secondary")
        self.cancel_btn.clicked.connect(self.reject)

        self.shutdown_btn = QPushButton("Shutdown System")
        self.shutdown_btn.setProperty("role", "danger")
        self.shutdown_btn.clicked.connect(self.accept)

        button_row.addStretch()
        button_row.addWidget(self.cancel_btn)
        button_row.addWidget(self.shutdown_btn)

        root.addLayout(button_row)


class MainWindow(QWidget):
    """
    Main Application Window – Production / Kiosk Ready

    - Fullscreen kiosk support
    - Secure shutdown
    - Zero wasted space
    - Deterministic layout
    """

    KIOSK_MODE = False  # Set to True for kiosk mode

    def __init__(self, signals):
        super().__init__()
        self.signals = signals

        self.setWindowTitle(WINDOW_TITLE)
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
        root.setContentsMargins(6, 6, 6, 6)
        root.setSpacing(6)

        # ---------------- HEADER ----------------
        self.header = HeaderWidget(
            on_print_clicked=self.open_pending_qr_window,
            on_settings_clicked=self.open_settings,
            on_shutdown_clicked=self.request_shutdown,
            kiosk_mode=self.KIOSK_MODE
        )

        root.addWidget(self.header)

        # ---------------- MAIN CONTENT ----------------
        content = QHBoxLayout()
        content.setSpacing(6)

        left = QVBoxLayout()
        left.setSpacing(6)

        self.plot_panel = PlotPanel()
        self.result_panel = ResultPanel()

        left.addWidget(self.plot_panel, stretch=7)
        left.addWidget(self.result_panel, stretch=3)

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
        self.signals.laser_value.connect(self.plot_panel.append_value)
        self.signals.cycle_detected.connect(self.on_cycle_detected)
        self.signals.laser_status.connect(self.on_laser_status)

        self.signals.plc_status.connect(self.footer.update_plc_status)
        modem_signals.modem_connected.connect(self.footer.update_modem_status)
        printer_signals.printer_status.connect(self.footer.update_printer_status)
        sms_signals.sms_sent.connect(self.footer.show_sms)

    # ============================================================
    # TIMERS
    # ============================================================
    def _init_timers(self):
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_datetime)
        self.clock_timer.start(1000)
        self._update_datetime()

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
        pwd = PasswordModal(self)
        if pwd.exec() != QDialog.Accepted:
            return

        dlg = SettingsWindow(self)
        dlg.settings_applied.connect(self.refresh_active_model)
        dlg.exec()

    # ============================================================
    # SHUTDOWN (ENHANCED, FACTORY SAFE – UNIFORM DIALOG)
    # ============================================================
    def request_shutdown(self):
        pwd = PasswordModal(self)
        if pwd.exec() != QDialog.Accepted:
            return

        dlg = ShutdownConfirmDialog(self)
        if dlg.exec() == QDialog.Accepted:
            self.close()



    # ============================================================
# PENDING QR PRINT WINDOW
# ============================================================
    def open_pending_qr_window(self):
        dlg = QRPrintDialog(self)
        dlg.exec()


    # ============================================================
    # MODEL
    # ============================================================
    def refresh_active_model(self):
        model = get_active_model()
        if not model:
            self.plot_panel.reset()
            self.plot_panel.reset_cycle_markers()
            return

        # ✅ This call already sets limits internally
        self.plot_panel.set_model_info(
            model["name"],
            model.get("model_type", "N/A"),
            float(model["lower_limit"]),
            float(model["upper_limit"])
        )

        # Clear old cycle overlays
        self.plot_panel.reset_cycle_markers()


    # ============================================================
    # CYCLES
    # ============================================================
    @Slot(dict)
    def on_cycle_detected(self, cycle: dict):
        if not cycle.get("completed", True):
            return

        # 🔹 NEW: update plot QC overlays (reference, min, depth band)
        self.plot_panel.update_cycle_result(cycle)

        # 🔹 Existing behavior
        self.result_panel.update_result(cycle)

        QTimer.singleShot(80, self.refresh_cycles)

        # ============================================================
    # REFRESH CYCLES LIST
    # ============================================================
    def refresh_cycles(self):
        try:
            cycles = get_cycles(limit=40)
        except Exception:
            cycles = []

        self.cycles_panel.update_cycles(cycles)

    # ============================================================
    # LASER STATUS
    # ============================================================
    @Slot(str)
    def on_laser_status(self, status: str):
        if status != "CONNECTED":
            self.plot_panel.show_no_data()
            self.result_panel.show_error("NO DATA")
