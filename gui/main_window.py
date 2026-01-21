from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QDialog,
    QLabel, QPushButton, QApplication
)
from PySide6.QtCore import QEvent

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

        self.title.setStyleSheet("font-size: 28pt; font-weight: bold; color: #f8fafc;")
        self.warning.setStyleSheet("font-size: 18pt; color: #94a3b8;")

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(22)

        self.title = QLabel("Exit Pneumatic Laser QC System?")
        self.title.setAlignment(Qt.AlignCenter)
        root.addWidget(self.title)

        self.warning = QLabel(
            "This will safely stop all system services and power down the application.\n\n"
            "Ensure no active welding cycle is in progress."
        )
        self.warning.setAlignment(Qt.AlignCenter)
        self.warning.setWordWrap(True)
        root.addWidget(self.warning)

        root.addStretch()

        buttons = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("role", "secondary")
        self.cancel_btn.clicked.connect(self.reject)

        self.shutdown_btn = QPushButton("Shutdown System")
        self.shutdown_btn.setProperty("role", "danger")
        self.shutdown_btn.clicked.connect(self.accept)

        buttons.addStretch()
        buttons.addWidget(self.cancel_btn)
        buttons.addWidget(self.shutdown_btn)
        root.addLayout(buttons)


# ============================================================
# MAIN WINDOW
# ============================================================
class MainWindow(QWidget):
    KIOSK_MODE = True  # Set to True to enable kiosk mode

    def __init__(self, signals):
        super().__init__()
        self.signals = signals

        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(1600, 900)

        self._build_ui()
        self._connect_signals()
        self._init_timers()
        self._init_cursor_hiding()

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

        self.header = HeaderWidget(
            on_print_clicked=self.open_pending_qr_window,
            on_settings_clicked=self.open_settings,
            on_history_clicked=self.open_history_window,  # ✅
            on_shutdown_clicked=self.request_shutdown,
            kiosk_mode=self.KIOSK_MODE
        )
        root.addWidget(self.header)

        content = QHBoxLayout()
        left = QVBoxLayout()

        self.plot_panel = PlotPanel()
        self.result_panel = ResultPanel()
        self.cycles_panel = CyclesPanel(kiosk_mode=self.KIOSK_MODE)

        left.addWidget(self.plot_panel, stretch=7)
        left.addWidget(self.result_panel, stretch=3)

        content.addLayout(left, stretch=4)
        content.addWidget(self.cycles_panel, stretch=1)

        root.addLayout(content, stretch=1)

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
    # CURSOR AUTO-HIDE (KIOSK SAFE)
    # ============================================================
    def _init_cursor_hiding(self):
        if not self.KIOSK_MODE:
            return

        self.cursor_hidden = False

        self.cursor_timer = QTimer(self)
        self.cursor_timer.setInterval(3000)  # 3 seconds
        self.cursor_timer.setSingleShot(True)
        self.cursor_timer.timeout.connect(self._hide_cursor)

        QApplication.instance().installEventFilter(self)
        self.cursor_timer.start()

    def _hide_cursor(self):
        if self.isActiveWindow() and not self.cursor_hidden:
            QApplication.setOverrideCursor(Qt.BlankCursor)
            self.cursor_hidden = True

    def _show_cursor(self):
        if self.cursor_hidden:
            QApplication.restoreOverrideCursor()
            self.cursor_hidden = False

    def eventFilter(self, obj, event):
        if self.KIOSK_MODE and self.isActiveWindow():
            if event.type() in (
                QEvent.MouseMove,
                QEvent.MouseButtonPress,
                QEvent.KeyPress,
                QEvent.Wheel,
                QEvent.TouchBegin,
                QEvent.TouchUpdate,
            ):
                self._show_cursor()
                self.cursor_timer.start()

        return super().eventFilter(obj, event)


    # ============================================================
    # SETTINGS / SHUTDOWN
    # ============================================================
    def open_settings(self):
        if PasswordModal(self).exec() != QDialog.Accepted:
            return
        dlg = SettingsWindow(self)
        dlg.settings_applied.connect(self.refresh_active_model)
        dlg.exec()

    def request_shutdown(self):
        if PasswordModal(self).exec() != QDialog.Accepted:
            return
        if ShutdownConfirmDialog(self).exec() == QDialog.Accepted:
            self.close()

    def open_pending_qr_window(self):
        QRPrintDialog(self).exec()

    # ============================================================
    # MODEL / CYCLES
    # ============================================================
    def refresh_active_model(self):
        model = get_active_model()
        if not model:
            self.plot_panel.reset()
            self.plot_panel.reset_cycle_markers()
            return

        self.plot_panel.set_model_info(
            model["name"],
            model.get("model_type", "N/A"),
            float(model["lower_limit"]),
            float(model["upper_limit"])
        )
        self.plot_panel.reset_cycle_markers()

    @Slot(dict)
    def on_cycle_detected(self, cycle: dict):
        if not cycle.get("completed", True):
            return

        self.plot_panel.update_cycle_result(cycle)
        self.result_panel.update_result(cycle)
        QTimer.singleShot(80, self.refresh_cycles)

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

    def open_history_window(self):
        if PasswordModal(self).exec() != QDialog.Accepted:
            return

        from gui.windows.history_window import HistoryWindow
        HistoryWindow(self).exec()
