# gui/widgets/header_widget.py

import os
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy
)
from PySide6.QtGui import QFont, QPixmap, QLinearGradient, QPalette, QBrush, QColor
from PySide6.QtCore import Qt, QSize


class HeaderWidget(QFrame):
    """
    Enhanced Application Header - Modern & Professional

    - Subtle gradient background with glow accent
    - Optional logo (left)
    - Bold company name
    - Live date & time (right)
    - Only Settings button is interactive
    - High contrast, dark-theme optimized
    """

    def __init__(self, on_settings_clicked, parent=None):
        super().__init__(parent)
        self.on_settings_clicked = on_settings_clicked
        self.setFixedHeight(72)  # Consistent modern header height
        self._build_ui()

    def _build_ui(self):
        self.setObjectName("HeaderWidget")
        self.setStyleSheet("""
            #HeaderWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #0f1622, stop:0.5 #0d1420, stop:1 #0a101a);
                border-bottom: 1px solid #1a3a5a;
                border-radius: 0px;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(20)

        # ---- Logo (optional) ----
        logo_lbl = QLabel()
        logo_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        logo_lbl.setFixedSize(48, 48)
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            if not pix.isNull():
                scaled_pix = pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                logo_lbl.setPixmap(scaled_pix)

        # ---- Company Name (prominent) ----
        company_lbl = QLabel("NTF ADVANCED COMPOSITES & ENGINEERING PLASTICS")
        company_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        company_lbl.setStyleSheet("""
            color: #00ccff;
            text-shadow: 0 0 8px rgba(0, 204, 255, 0.4);
        """)
        company_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        company_lbl.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)

        


                # ---- Date & Time (live update) ----
        self.datetime_lbl = QLabel("")
        self.datetime_lbl.setFont(QFont("Segoe UI", 15, QFont.DemiBold))  # Fixed: SemiBold → DemiBold
        self.datetime_lbl.setStyleSheet("color: #66bbff;")
        self.datetime_lbl.setAlignment(Qt.AlignVCenter | Qt.AlignRight)

        # ---- Settings Button (only interactive element) ----
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedSize(110, 38)
        settings_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        settings_btn.setCursor(Qt.PointingHandCursor)
        settings_btn.clicked.connect(self.on_settings_clicked)
        settings_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a5fb3, stop:1 #0f4299);
                color: white;
                border: 1px solid #2a7fd4;
                border-radius: 8px;
                padding: 0px 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2470d0, stop:1 #1855b8);
                border: 1px solid #3a9eff;
            }
            QPushButton:pressed {
                background: #0d3680;
                border: 1px solid #1a5fb3;
            }
        """)

        # ---- Assemble Layout ----
        if logo_lbl.pixmap() is not None:
            layout.addWidget(logo_lbl, alignment=Qt.AlignVCenter)

        layout.addWidget(company_lbl, alignment=Qt.AlignVCenter)
        layout.addStretch()
        layout.addWidget(self.datetime_lbl, alignment=Qt.AlignVCenter)
        layout.addSpacing(16)
        layout.addWidget(settings_btn, alignment=Qt.AlignVCenter)

    # --------------------------------------------------
    # Public API
    # --------------------------------------------------
    def set_datetime(self, text: str):
        """Update the current date and time display"""
        self.datetime_lbl.setText(text)