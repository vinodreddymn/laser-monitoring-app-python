import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QWidget
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt, QTimer


class FooterWidget(QFrame):
    """
    Industrial Footer Widget (Strictly Flat Design)

    - Left: Compact status indicators
    - Center/Right: Branding OR SMS (mutually exclusive)
    - SMS shown only when sent (failed cycles)
    - Status dot blinks ONLY when disconnected
    - NO shadows, NO effects, NO boxes
    """

    HEIGHT = 60
    SMS_VISIBLE_MS = 15000

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.HEIGHT)

        self._blink_timers = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #0a101a;
                border-top: 1px solid #1a3a5a;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(16, 8, 16, 8)
        root.setSpacing(20)

        # ================= LEFT: STATUS =================
        self.status_bar = QWidget()
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(18)

        self.modem = self._create_status("Modem")
        self.plc = self._create_status("PLC")
        self.laser = self._create_status("Laser")

        status_layout.addWidget(self.modem)
        status_layout.addWidget(self.plc)
        status_layout.addWidget(self.laser)

        root.addWidget(self.status_bar)

        # ================= RIGHT: INFO (SMS / BRANDING) =================
        self.info_container = QWidget()
        info_layout = QHBoxLayout(self.info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(8)

        # Branding (default)
        self.brand_logo = QLabel()
        logo_path = os.path.join("assets", "ashtech_logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            if not pix.isNull():
                self.brand_logo.setPixmap(
                    pix.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

        self.brand_text = QLabel("Ashtech Engineering Solutions")
        self.brand_text.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.brand_text.setStyleSheet("color:#88ccff;")

        # SMS label (hidden by default)
        self.sms_label = QLabel("")
        self.sms_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.sms_label.setStyleSheet("color:#00ff88;")
        self.sms_label.hide()

        info_layout.addWidget(self.brand_logo)
        info_layout.addWidget(self.brand_text)
        info_layout.addWidget(self.sms_label)

        root.addStretch()
        root.addWidget(self.info_container)

        # SMS auto-hide timer
        self.sms_timer = QTimer(self)
        self.sms_timer.setSingleShot(True)
        self.sms_timer.timeout.connect(self._hide_sms)

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------
    def _create_status(self, name: str) -> QWidget:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        l.setSpacing(6)

        dot = QLabel("●")
        dot.setFont(QFont("Segoe UI", 13))
        dot.setStyleSheet("color:#666;")

        label = QLabel(f"{name}: ---")
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet("color:#cccccc;")

        l.addWidget(dot)
        l.addWidget(label)

        w.dot = dot
        w.label = label
        w.blink_on = False
        return w

    def _set_status(self, widget, name: str, connected: bool):
        widget.label.setText(
            f"{name}: {'CONNECTED' if connected else 'DISCONNECTED'}"
        )

        if connected:
            widget.dot.setStyleSheet("color:#00ff88;")
            self._stop_blink(widget)
        else:
            widget.dot.setStyleSheet("color:#ff4444;")
            self._start_blink(widget)

    # ------------------------------------------------------------------
    # Blink logic (ONLY for disconnected)
    # ------------------------------------------------------------------
    def _start_blink(self, widget):
        if widget.blink_on:
            return

        timer = QTimer(self)
        timer.setInterval(600)

        def toggle():
            widget.dot.setVisible(not widget.dot.isVisible())

        timer.timeout.connect(toggle)
        timer.start()

        self._blink_timers[widget] = timer
        widget.blink_on = True

    def _stop_blink(self, widget):
        timer = self._blink_timers.pop(widget, None)
        if timer:
            timer.stop()
        widget.dot.setVisible(True)
        widget.blink_on = False

    # ------------------------------------------------------------------
    # SMS handling (FAILED cycles only)
    # ------------------------------------------------------------------
    def show_sms(self, info: dict):
        msg = info.get("message", "").strip()
        name = info.get("name", "Unknown")
        phone = info.get("phone", "---")

        self.sms_label.setText(
            f'SMS SENT → {name} ({phone}) | "{msg}"'
        )

        # Hide branding
        self.brand_logo.hide()
        self.brand_text.hide()

        # Show SMS
        self.sms_label.show()

        self.sms_timer.start(self.SMS_VISIBLE_MS)

    def _hide_sms(self):
        self.sms_label.hide()
        self.sms_label.setText("")

        self.brand_logo.show()
        self.brand_text.show()

    # ------------------------------------------------------------------
    # Public status API
    # ------------------------------------------------------------------
    def update_modem_status(self, connected: bool):
        self._set_status(self.modem, "Modem", connected)

    def update_plc_status(self, status: dict):
        self._set_status(self.plc, "PLC", status.get("connected", False))

    def update_laser_status(self, status: str):
        self._set_status(self.laser, "Laser", status == "CONNECTED")
