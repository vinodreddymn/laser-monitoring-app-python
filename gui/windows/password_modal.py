# gui/windows/password_modal.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from config.app_config import verify_settings_password
from gui.styles.app_styles import apply_base_dialog_style


class PasswordModal(QDialog):
    """
    Password Modal Dialog – Production Safe

    Purpose:
    - Protect access to Settings
    - Keyboard-friendly (Enter = Unlock, Esc = Cancel)

    Styling:
    - Internal (apply_base_dialog_style)
    """

    WIDTH = 550
    HEIGHT = 300

    # -------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("PasswordDialog")
        self.setWindowTitle("Settings Access")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()

        # Apply centralized internal styling
        apply_base_dialog_style(self)

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        # ---------------- Title ----------------
        title = QLabel("Enter Settings Password")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        subtitle = QLabel(
            "Authentication is required to access system settings."
        )
        subtitle.setObjectName("MutedText")
        subtitle.setAlignment(Qt.AlignCenter)

        root.addWidget(title)
        root.addWidget(subtitle)

        # ---------------- Password Input ----------------
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Password")
        self.password_input.setClearButtonEnabled(True)
        self.password_input.setFont(QFont("Segoe UI", 11))
        self.password_input.setFocus()

        root.addWidget(self.password_input)

        # ---------------- Buttons ----------------
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("role", "secondary")
        self.cancel_btn.clicked.connect(self.reject)

        self.ok_btn = QPushButton("Unlock")
        self.ok_btn.setProperty("role", "primary")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._verify_password)

        button_row.addStretch()
        button_row.addWidget(self.cancel_btn)
        button_row.addWidget(self.ok_btn)

        root.addLayout(button_row)

        # ---------------- Keyboard shortcuts ----------------
        self.password_input.returnPressed.connect(self._verify_password)

    # -------------------------------------------------
    # Logic
    # -------------------------------------------------
    def _verify_password(self):
        entered = self.password_input.text().strip()

        if verify_settings_password(entered):
            self.accept()
            return

        QMessageBox.warning(
            self,
            "Access Denied",
            "Incorrect password.\nPlease try again."
        )

        self.password_input.clear()
        self.password_input.setFocus()