# gui/widgets/header_widget.py

import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtCore import Qt


class HeaderWidget(QFrame):
    """
    Enhanced Application Header – Modern & Professional

    - Fixed 60px industrial header
    - Subtle gradient background
    - Optimized for large logo (1685 × 510 px)
    - Transparent labels & logo
    - Live date & time
    - Single interactive Settings button
    """

    HEADER_HEIGHT = 60
    LOGO_HEIGHT = 36

    def __init__(self, on_settings_clicked, parent=None):
        super().__init__(parent)
        self.on_settings_clicked = on_settings_clicked

        # --- Header height control ---
        self.setFixedHeight(self.HEADER_HEIGHT)

        self._build_ui()

    # --------------------------------------------------
    # UI Builder
    # --------------------------------------------------
    def _build_ui(self):
        self.setObjectName("HeaderWidget")

        # --- Header background ---
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

        # --- Layout ---
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 6, 20, 6)
        layout.setSpacing(16)

        # --------------------------------------------------
        # Logo (transparent background)
        # --------------------------------------------------
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        logo_lbl.setFixedHeight(self.LOGO_HEIGHT)
        logo_lbl.setStyleSheet("background: transparent;")

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            if not pixmap.isNull():
                logo_lbl.setPixmap(
                    pixmap.scaledToHeight(
                        self.LOGO_HEIGHT,
                        Qt.SmoothTransformation
                    )
                )

        # --------------------------------------------------
        # Company Name
        # --------------------------------------------------
        company_lbl = QLabel("ASHTECH ENGINEERING SOLUTIONS")
        company_lbl.setFont(QFont("Segoe UI", 18, QFont.Bold))
        company_lbl.setStyleSheet("""
            background: transparent;
            color: #7dd3fc;
            letter-spacing: 0.5px;
        """)
        company_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        company_lbl.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred
        )

        # --------------------------------------------------
        # Date & Time
        # --------------------------------------------------
        self.datetime_lbl = QLabel("")
        self.datetime_lbl.setFont(QFont("Segoe UI", 15, QFont.DemiBold))
        self.datetime_lbl.setStyleSheet("""
            background: transparent;
            color: #93c5fd;
        """)
        self.datetime_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # --------------------------------------------------
        # Settings Button
        # --------------------------------------------------
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedSize(120, 34)
        settings_btn.setFont(QFont("Segoe UI", 15, QFont.Bold))
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.clicked.connect(self.on_settings_clicked)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a5fb3,
                    stop:1 #0f4299
                );
                color: white;
                border: 1px solid #2a7fd4;
                border-radius: 7px;
                padding: 0px 14px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2470d0,
                    stop:1 #1855b8
                );
                border: 1px solid #3a9eff;
            }
            QPushButton:pressed {
                background: #0d3680;
                border: 1px solid #1a5fb3;
            }
        """)

        # --------------------------------------------------
        # Assemble Layout
        # --------------------------------------------------
        if logo_lbl.pixmap() is not None:
            layout.addWidget(logo_lbl)

        layout.addWidget(company_lbl)
        layout.addStretch()
        layout.addWidget(self.datetime_lbl)
        layout.addSpacing(12)
        layout.addWidget(settings_btn)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def set_datetime(self, text: str):
        """Update the current date and time display"""
        self.datetime_lbl.setText(text)
