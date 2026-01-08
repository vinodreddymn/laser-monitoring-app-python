import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,   # <-- ADD THIS
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QLabel,
    QFrame
)

from PySide6.QtCore import Qt

from config.app_config import (
    verify_settings_password,
    update_settings_password
)
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class ChangePasswordTab(QWidget):
    """
    Change Settings Password – Supervisor Access

    Purpose
    -------
    • Change system settings password
    • Used to protect configuration screens
    • Plain-text password (intentional for kiosk systems)

    Design
    ------
    • Clear instructions
    • No ambiguity
    • Stable, distraction-free UI
    """

    # --------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self._build_ui()
        apply_base_dialog_style(self)

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(22)

        # ---------------- Header ----------------
        header = QLabel("Change Settings Password")
        header.setObjectName("SectionTitle")

        subtitle = QLabel(
            "This password protects access to system configuration screens."
        )
        subtitle.setObjectName("MutedText")

        root.addWidget(header)
        root.addWidget(subtitle)

        # ---------------- Divider ----------------
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        root.addWidget(divider)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)

        self.current_pwd = QLineEdit()
        self.current_pwd.setEchoMode(QLineEdit.Password)
        self.current_pwd.setPlaceholderText("Current password")

        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd.setPlaceholderText("New password")

        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        self.confirm_pwd.setPlaceholderText("Confirm new password")

        form.addRow("Current Password", self.current_pwd)
        form.addRow("New Password", self.new_pwd)
        form.addRow("Confirm Password", self.confirm_pwd)

        root.addLayout(form)

        # ---------------- Action Row ----------------
        action_row = QHBoxLayout()
        self.btn_change = QPushButton("Update Password")
        self.btn_change.setProperty("role", "primary")
        self.btn_change.setMinimumWidth(220)
        self.btn_change.clicked.connect(self._change_password)

        action_row.addWidget(self.btn_change)
        action_row.addStretch()

        root.addLayout(action_row)
        root.addStretch()

    # ==================================================
    # LOGIC
    # ==================================================
    def _change_password(self):
        current = self.current_pwd.text().strip()
        new = self.new_pwd.text().strip()
        confirm = self.confirm_pwd.text().strip()

        # ---------------- Validation ----------------
        if not current or not new or not confirm:
            QMessageBox.warning(
                self,
                "Missing Information",
                "All password fields are required."
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
                "Password Mismatch",
                "New password and confirmation do not match."
            )
            self.confirm_pwd.setFocus()
            return

        # ---------------- Update ----------------
        try:
            update_settings_password(new)

            QMessageBox.information(
                self,
                "Password Updated",
                "Settings password has been updated successfully."
            )

            self._clear_fields()

        except Exception:
            log.exception("Settings password update failed")
            QMessageBox.critical(
                self,
                "Update Failed",
                "Unable to update the settings password.\n"
                "Please check system logs."
            )

    # --------------------------------------------------
    def _clear_fields(self):
        self.current_pwd.clear()
        self.new_pwd.clear()
        self.confirm_pwd.clear()
        self.current_pwd.setFocus()
