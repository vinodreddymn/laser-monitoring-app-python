import os

from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt


class HeaderWidget(QFrame):
    """
    Application Header – Kiosk Aware

    - Fixed 60px industrial header
    - Gradient background
    - Logo + company name
    - Live date & time
    - Icon-only Print button
    - Icon-only Settings button
    - Shutdown icon (ONLY in kiosk mode)
    """

    HEADER_HEIGHT = 60
    LOGO_HEIGHT = 36
    ICON_BTN_SIZE = (38, 34)

    def __init__(
        self,
        on_print_clicked,
        on_settings_clicked,
        on_history_clicked,   # ✅ NEW
        on_shutdown_clicked=None,
        kiosk_mode: bool = False,
        parent=None
    ):
        super().__init__(parent)

        self.on_print_clicked = on_print_clicked
        self.on_settings_clicked = on_settings_clicked
        self.on_history_clicked = on_history_clicked   # ✅ FIX
        self.on_shutdown_clicked = on_shutdown_clicked
        self.kiosk_mode = kiosk_mode

        self.setFixedHeight(self.HEADER_HEIGHT)
        self._build_ui()

    # --------------------------------------------------
    def _build_ui(self):
        self.setObjectName("HeaderWidget")

        # ---------------- Header Style ----------------
        self.setStyleSheet("""
            #HeaderWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1622,
                    stop:0.5 #0d1420,
                    stop:1 #0a101a
                );
                border-bottom: 1px solid #1a3a5a;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.setSpacing(12)

        # ---------------- Logo ----------------
        logo = QLabel()
        logo.setFixedHeight(self.LOGO_HEIGHT)
        logo.setStyleSheet("background: transparent;")

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                logo.setPixmap(
                    pixmap.scaledToHeight(
                        self.LOGO_HEIGHT,
                        Qt.SmoothTransformation
                    )
                )

        # ---------------- Company Name ----------------
        company = QLabel("ASHTECH ENGINEERING SOLUTIONS")
        company.setFont(QFont("Segoe UI", 18, QFont.Bold))
        company.setStyleSheet("color:#7dd3fc; background:transparent;")
        company.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # ---------------- Date / Time ----------------
        self.datetime_lbl = QLabel("")
        self.datetime_lbl.setFont(QFont("Segoe UI", 15, QFont.DemiBold))
        self.datetime_lbl.setStyleSheet(
            "color:#93c5fd; background:transparent;"
        )

        # ---------------- Common Icon Button Style ----------------
        icon_btn_style = """
            QPushButton {
                background: transparent;
                color: #e5e7eb;
                border: 1px solid #334155;
                border-radius: 7px;
            }
            QPushButton:hover {
                background: #1e293b;
            }
            QPushButton:pressed {
                background: #020617;
            }
        """
        history_btn = QPushButton("📜")
        history_btn.setFixedSize(*self.ICON_BTN_SIZE)
        history_btn.setFont(QFont("Segoe UI", 16))
        history_btn.setCursor(Qt.PointingHandCursor)
        history_btn.setToolTip("Cycle History")
        history_btn.clicked.connect(self.on_history_clicked)
        history_btn.setStyleSheet(icon_btn_style)


        # ---------------- PRINT (ICON ONLY) ----------------
        print_btn = QPushButton("🖨")
        print_btn.setFixedSize(*self.ICON_BTN_SIZE)
        print_btn.setFont(QFont("Segoe UI", 16))
        print_btn.setCursor(Qt.PointingHandCursor)
        print_btn.setToolTip("Print pending QR labels")
        print_btn.clicked.connect(self.on_print_clicked)
        print_btn.setStyleSheet(icon_btn_style)

        # ---------------- SETTINGS (ICON ONLY) ----------------
        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(*self.ICON_BTN_SIZE)
        settings_btn.setFont(QFont("Segoe UI", 17))
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.setToolTip("Application settings")
        settings_btn.clicked.connect(self.on_settings_clicked)
        settings_btn.setStyleSheet(icon_btn_style)

        # ---------------- Assemble Left → Right ----------------
        layout.addWidget(logo)
        layout.addWidget(company)
        layout.addStretch()
        layout.addWidget(self.datetime_lbl)
        layout.addSpacing(12)
        layout.addWidget(print_btn)
        layout.addSpacing(6)
        layout.addWidget(history_btn)   # ✅
        layout.addSpacing(6)
        layout.addWidget(settings_btn)

        # ---------------- SHUTDOWN (KIOSK ONLY) ----------------
        if self.kiosk_mode and self.on_shutdown_clicked:
            shutdown_btn = QPushButton("⏻")
            shutdown_btn.setFixedSize(*self.ICON_BTN_SIZE)
            shutdown_btn.setFont(QFont("Segoe UI", 18, QFont.Bold))
            shutdown_btn.setCursor(Qt.PointingHandCursor)
            shutdown_btn.setToolTip("Shutdown application")
            shutdown_btn.clicked.connect(self.on_shutdown_clicked)
            shutdown_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #ef4444;
                    border: 1px solid #7f1d1d;
                    border-radius: 7px;
                }
                QPushButton:hover {
                    background: #7f1d1d;
                    color: white;
                }
                QPushButton:pressed {
                    background: #991b1b;
                }
            """)
            layout.addSpacing(6)
            layout.addWidget(shutdown_btn)

    # --------------------------------------------------
    def set_datetime(self, text: str):
        """Update live date/time label"""
        self.datetime_lbl.setText(text)
