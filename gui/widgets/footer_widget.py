# gui/widgets/footer_widget.py

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QWidget, QScrollArea
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

from backend.usb_printer_manager import printer_signals, usb_printer
from backend.gsm_modem import modem_signals, gsm
from backend.plc_status import plc_listener


class FooterWidget(QFrame):
    """
    Industrial Footer – FINAL (Header Matched & Scoped)

    - Same gradient as HeaderWidget
    - Fixed 60px height
    - Properly scoped styles (no QWidget bleed)
    - Header-matched typography
    - Color-enhanced SMS sections
    - No blinking indicators
    - Scroll only if needed
    - 2s pause BEFORE scroll
    - Full scroll
    - 2s pause at END before restart
    - Auto-clear SMS
    """

    HEIGHT = 60

    SMS_VISIBLE_MS = 15000
    SCROLL_INTERVAL_MS = 30
    SCROLL_STEP = 1
    START_PAUSE_MS = 2000
    END_PAUSE_MS = 2000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("FooterWidget")
        self.setFixedHeight(self.HEIGHT)

        self._scroll_limit = 0
        self._sms_active = False

        # Timers
        self.scroll_timer = QTimer(self)
        self.scroll_timer.timeout.connect(self._scroll_sms)

        self.start_pause_timer = QTimer(self)
        self.start_pause_timer.setSingleShot(True)
        self.start_pause_timer.timeout.connect(self._start_scroll)

        self.end_pause_timer = QTimer(self)
        self.end_pause_timer.setSingleShot(True)
        self.end_pause_timer.timeout.connect(self._restart_scroll_if_valid)

        self.sms_clear_timer = QTimer(self)
        self.sms_clear_timer.setSingleShot(True)
        self.sms_clear_timer.timeout.connect(self._clear_sms)

        self._build_ui()
        self._connect_signals()

        # Request initial states
        usb_printer.emit_current_status()
        gsm.emit_current_status()
        plc_listener.emit_current_status()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        # IMPORTANT: Scoped stylesheet (matches HeaderWidget logic)
        self.setStyleSheet("""
        #FooterWidget {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #0f1622,
                stop:0.5 #0d1420,
                stop:1 #0a101a
            );
        }

        #FooterWidget QLabel,
        #FooterWidget QWidget,
        #FooterWidget QScrollArea,
        #FooterWidget QScrollArea QWidget {
            background: transparent;
            border: none;
        }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 6, 20, 6)
        root.setSpacing(16)

        # -------- Status labels --------
        self.modem_lbl = self._create_status_label("Modem")
        self.plc_lbl = self._create_status_label("PLC")
        self.printer_lbl = self._create_status_label("Printer")

        root.addWidget(self.modem_lbl)
        root.addWidget(self.plc_lbl)
        root.addWidget(self.printer_lbl)
        root.addStretch()

        # -------- SMS area --------
        self.sms_scroll = QScrollArea()
        self.sms_scroll.setFrameShape(QFrame.NoFrame)
        self.sms_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sms_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.sms_scroll.setWidgetResizable(True)
        self.sms_scroll.setFixedHeight(28)

        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch()

        self.sms_label = QLabel("")
        self.sms_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.sms_label.setTextFormat(Qt.RichText)
        self.sms_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.sms_label.setWordWrap(False)

        layout.addWidget(self.sms_label)
        self.sms_scroll.setWidget(container)

        root.addWidget(self.sms_scroll, stretch=1)

    def _create_status_label(self, name: str) -> QLabel:
        lbl = QLabel(f"{name}: ---")
        lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
        lbl.setStyleSheet("color:#cbd5f5;")
        lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        return lbl

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------
    def _connect_signals(self):
        modem_signals.modem_connected.connect(self.update_modem)
        plc_listener.plc_status_changed.connect(self.update_plc)
        printer_signals.printer_status.connect(self.update_printer)

    # --------------------------------------------------
    # Status updates
    # --------------------------------------------------
    def update_modem(self, connected: bool):
        self._set_status(self.modem_lbl, "Modem", connected)

    def update_plc(self, status: dict):
        self._set_status(self.plc_lbl, "PLC", status.get("power", False))

    def update_printer(self, connected: bool, name: str):
        extra = f" ({name})" if connected and name else ""
        self._set_status(self.printer_lbl, "Printer", connected, extra)

    def _set_status(self, label: QLabel, name: str, ok: bool, extra: str = ""):
        color = "#22c55e" if ok else "#ef4444"
        state = "CONNECTED" if ok else "DISCONNECTED"
        label.setText(f"{name}: {state}{extra}")
        label.setStyleSheet(f"color:{color};")

    # --------------------------------------------------
    # SMS handling
    # --------------------------------------------------
    def show_sms(self, info: dict):
        name = info.get("name", "Unknown")
        phone = info.get("phone", "-")
        message = info.get("message", "")
        time_str = info.get("time", "")

        html = (
            '<span style="color:#38bdf8;">SMS SENT</span> '
            f'<span style="color:#7dd3fc;">{name}</span> '
            f'<span style="color:#fde68a;">({phone})</span> '
            f'<span style="color:#93c5fd;">[{time_str}]</span>'
            ' <span style="color:#64748b;">—</span> '
            f'<span style="color:#22c55e;">{message}</span>'
        )

        self.sms_label.setText(html)
        self._sms_active = True

        self._prepare_scroll()
        self.sms_clear_timer.start(self.SMS_VISIBLE_MS)

    def _prepare_scroll(self):
        bar = self.sms_scroll.horizontalScrollBar()
        bar.setValue(0)

        self.scroll_timer.stop()
        self.start_pause_timer.stop()
        self.end_pause_timer.stop()

        label_width = self.sms_label.sizeHint().width()
        viewport_width = self.sms_scroll.viewport().width()
        self._scroll_limit = label_width + viewport_width

        if label_width > viewport_width:
            self.start_pause_timer.start(self.START_PAUSE_MS)

    def _start_scroll(self):
        if self._sms_active:
            self.scroll_timer.start(self.SCROLL_INTERVAL_MS)

    def _scroll_sms(self):
        bar = self.sms_scroll.horizontalScrollBar()
        value = bar.value() + self.SCROLL_STEP

        if value > self._scroll_limit:
            self.scroll_timer.stop()
            if self._sms_active:
                self.end_pause_timer.start(self.END_PAUSE_MS)
            return

        bar.setValue(value)

    def _restart_scroll_if_valid(self):
        if self._sms_active:
            self.sms_scroll.horizontalScrollBar().setValue(0)
            self.start_pause_timer.start(self.START_PAUSE_MS)

    def _clear_sms(self):
        self._sms_active = False
        self.scroll_timer.stop()
        self.start_pause_timer.stop()
        self.end_pause_timer.stop()
        self.sms_label.setText("")

    # --------------------------------------------------
    # Backward compatibility
    # --------------------------------------------------
    def update_modem_status(self, connected: bool):
        self.update_modem(connected)

    def update_printer_status(self, connected: bool, name: str):
        self.update_printer(connected, name)

    def update_plc_status(self, status: dict):
        self.update_plc(status)
