# gui/header_widget.py

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class HeaderWidget(QFrame):
    def __init__(self, on_settings_clicked, parent=None):
        super().__init__(parent)

        self.on_settings_clicked = on_settings_clicked

        self.model_name_label = None
        self.model_limits_label = None
        self.clock_label = None

        self._build()

    def _build(self):
        self.setObjectName("headerWidget")
        self.setFixedHeight(90)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 10, 20, 10)
        main_layout.setSpacing(20)

        # ---------------------------------------------------------
        # LEFT: Logo + Company Branding
        # ---------------------------------------------------------
        left_container = QHBoxLayout()
        left_container.setSpacing(12)

        self.logo_label = QLabel()
        self.logo_label.setObjectName("headerLogo")

        try:
            pixmap = QPixmap("assets/logo.png")
            self.logo_label.setPixmap(
                pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        except Exception:
            self.logo_label.setText("LOGO")

        left_container.addWidget(self.logo_label)

        name_box = QVBoxLayout()
        name_box.setSpacing(2)

        self.company_label = QLabel("NTF ADVANCED COMPOSITES")
        self.company_label.setObjectName("companyLabel")

        self.app_label = QLabel("Pneumatic QC Monitor")
        self.app_label.setObjectName("appLabel")

        name_box.addWidget(self.company_label)
        name_box.addWidget(self.app_label)

        left_container.addLayout(name_box)

        main_layout.addLayout(left_container)

        # ---------------------------------------------------------
        # CENTER: Spacer (keeps titles centered cleanly)
        # ---------------------------------------------------------
        main_layout.addStretch(1)

        # ---------------------------------------------------------
        # RIGHT: Model Info + Clock + Settings
        # ---------------------------------------------------------
        right_container = QHBoxLayout()
        right_container.setSpacing(16)

        # Model info box
        model_box = QVBoxLayout()
        model_box.setSpacing(2)

        self.model_name_label = QLabel("Model: —")
        self.model_name_label.setObjectName("modelNameLabel")

        self.model_limits_label = QLabel("Limits: —")
        self.model_limits_label.setObjectName("modelLimitsLabel")

        model_box.addWidget(self.model_name_label)
        model_box.addWidget(self.model_limits_label)

        right_container.addLayout(model_box)

        # Clock
        self.clock_label = QLabel("--:--:--")
        self.clock_label.setObjectName("clockLabel")
        self.clock_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.clock_label.setMinimumWidth(120)

        right_container.addWidget(self.clock_label)

        # Settings button
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.setObjectName("settingsButton")
        self.settings_btn.setCursor(Qt.PointingHandCursor)
        self.settings_btn.clicked.connect(self.on_settings_clicked)

        right_container.addWidget(self.settings_btn)

        main_layout.addLayout(right_container)

    # ---------------------------------------------------------
    # PUBLIC UPDATE METHODS
    # ---------------------------------------------------------

    def update_model_info(self, name: str, lower: float, upper: float):
        self.model_name_label.setText(f"Model: {name}")
        self.model_limits_label.setText(f"Limits: {lower:.1f} – {upper:.1f} mm")

    def update_clock(self, text: str):
        self.clock_label.setText(text)
