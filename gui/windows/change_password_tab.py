# gui/windows/change_password_tab.py

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from config.app_config import (
    verify_settings_password,
    update_settings_password
)
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class ChangePasswordTab(QWidget):
    """
    Change Settings Password Tab

    Purpose:
    - Allow admin to change settings password
    - Plain-text password (intentional for kiosk system)

    Styling:
    - Internal (apply_base_dialog_style)
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self._build_ui()
        apply_base_dialog_style(self)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        # ---------------- Title ----------------
        title = QLabel("Change Settings Password")
        title.setObjectName("SectionTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignLeft)

        subtitle = QLabel(
            "This password is required to access system settings."
        )
        subtitle.setObjectName("MutedText")

        root.addWidget(title)
        root.addWidget(subtitle)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.current_pwd = QLineEdit()
        self.current_pwd.setEchoMode(QLineEdit.Password)
        self.current_pwd.setPlaceholderText("Enter current password")

        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd.setPlaceholderText("Enter new password")

        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        self.confirm_pwd.setPlaceholderText("Re-enter new password")

        form.addRow("Current Password:", self.current_pwd)
        form.addRow("New Password:", self.new_pwd)
        form.addRow("Confirm Password:", self.confirm_pwd)

        root.addLayout(form)

        # ---------------- Action Button ----------------
        self.btn_change = QPushButton("Update Password")
        self.btn_change.setProperty("role", "primary")
        self.btn_change.setFixedWidth(200)
        self.btn_change.clicked.connect(self._change_password)

        root.addWidget(self.btn_change, alignment=Qt.AlignLeft)
        root.addStretch()

    # --------------------------------------------------
    # Logic
    # --------------------------------------------------
    def _change_password(self):
        current = self.current_pwd.text().strip()
        new = self.new_pwd.text().strip()
        confirm = self.confirm_pwd.text().strip()

        if not current or not new or not confirm:
            QMessageBox.warning(
                self,
                "Missing Information",
                "All fields are required."
            )
            return

        if not verify_settings_password(current):
            QMessageBox.critical(
                self,
                "Access Denied",
                "Current password is incorrect."
            )
            self.current_pwd.setFocus()
            return

        if new != confirm:
            QMessageBox.warning(
                self,
                "Mismatch",
                "New password and confirmation do not match."
            )
            self.confirm_pwd.setFocus()
            return

        try:
            update_settings_password(new)

            QMessageBox.information(
                self,
                "Password Updated",
                "Settings password updated successfully."
            )

            self.current_pwd.clear()
            self.new_pwd.clear()
            self.confirm_pwd.clear()

        except Exception:
            log.exception("Password update failed")
            QMessageBox.critical(
                self,
                "Error",
                "Failed to update password."
            )
