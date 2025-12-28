from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from config.app_config import SETTINGS_PASSWORD


class PasswordModal(QDialog):
    """
    Password Modal Dialog – Production Safe

    Purpose:
    - Protect access to Settings
    - Keyboard-friendly (Enter = Unlock, Esc = Cancel)

    Styling:
    - styles/dialogs.qss
    """

    WIDTH = 360
    HEIGHT = 180

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("PasswordDialog")
        self.setWindowTitle("Settings Access")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()

    # -------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------
        title = QLabel("Enter Settings Password")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        layout.addWidget(title)

        # -------------------------------------------------
        # Password Input
        # -------------------------------------------------
        self.password_input = QLineEdit()
        self.password_input.setObjectName("PasswordInput")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setClearButtonEnabled(True)
        self.password_input.setFont(QFont("Segoe UI", 11))
        self.password_input.setFocus()

        layout.addWidget(self.password_input)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setObjectName("DialogCancelButton")
        self.cancel_btn.setProperty("role", "secondary")
        self.cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton("Unlock")
        self.ok_btn.setObjectName("DialogPrimaryButton")
        self.ok_btn.setProperty("role", "primary")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._verify_password)

        button_row.addStretch()
        button_row.addWidget(self.cancel_btn)
        button_row.addWidget(self.ok_btn)

        layout.addLayout(button_row)

        # -------------------------------------------------
        # Keyboard shortcuts
        # -------------------------------------------------
        self.password_input.returnPressed.connect(self._verify_password)

    # -------------------------------------------------
    def _verify_password(self):
        entered = self.password_input.text().strip()

        if entered == SETTINGS_PASSWORD:
            self.accept()
            return

        QMessageBox.warning(
            self,
            "Access Denied",
            "Incorrect password.\nPlease try again."
        )

        self.password_input.clear()
        self.password_input.setFocus()
