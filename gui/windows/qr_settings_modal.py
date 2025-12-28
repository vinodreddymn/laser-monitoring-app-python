from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QLabel, QDialogButtonBox,
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.settings_dao import get_qr_settings, save_qr_settings


class QRSettingsModal(QDialog):
    """
    QR Settings Modal – Qt Native (Production Safe)

    Purpose:
    - Configure QR prefix & counter
    - Preview next QR code
    - Model type is READ-ONLY (comes from model)

    Styling:
    - styles/dialogs.qss
    """

    WIDTH = 460
    HEIGHT = 360

    def __init__(self, parent=None, model=None, callback=None):
        super().__init__(parent)

        self.model = model or {}
        self.callback = callback

        self.setObjectName("QRSettingsModal")
        self.setWindowTitle(f"Activate Model: {self.model.get('name', '')}")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._load_settings()
        self._build_ui()

    # --------------------------------------------------
    def _load_settings(self):
        settings = get_qr_settings() or {}

        self.qr_prefix = settings.get(
            "qr_text_prefix",
            self.model.get("name", "Part")
        )
        self.qr_counter = int(
            settings.get("qr_start_counter", 1)
        )
        self.model_type = self.model.get("model_type", "RHD")

    # --------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(20)

        # --------------------------------------------------
        # Title
        # --------------------------------------------------
        title = QLabel(
            f"Activate Model: {self.model.get('name', '')} "
            f"({self.model_type})"
        )
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        # --------------------------------------------------
        # Form
        # --------------------------------------------------
        form = QFormLayout()
        form.setSpacing(14)

        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.counter_edit = QLineEdit(str(self.qr_counter))

        self.prefix_edit.setPlaceholderText("QR text prefix")
        self.counter_edit.setPlaceholderText("Starting counter")

        self.counter_edit.setMaximumWidth(160)

        form.addRow("QR Text Prefix:", self.prefix_edit)
        form.addRow("Starting Counter:", self.counter_edit)

        layout.addLayout(form)

        # --------------------------------------------------
        # Preview
        # --------------------------------------------------
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self.preview_label.setObjectName("QRPreview")

        layout.addWidget(self.preview_label)

        self.prefix_edit.textChanged.connect(self._update_preview)
        self.counter_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        # --------------------------------------------------
        # Buttons
        # --------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("Activate & Save")
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    # --------------------------------------------------
    def _update_preview(self):
        prefix = self.prefix_edit.text().strip() or "Text"
        try:
            counter = int(self.counter_edit.text())
        except ValueError:
            counter = 1

        self.preview_label.setText(
            f"Next QR → {prefix}.{str(counter).zfill(5)}"
        )

    # --------------------------------------------------
    def _save(self):
        prefix = self.prefix_edit.text().strip()
        try:
            counter = int(self.counter_edit.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Counter",
                "Starting counter must be a number."
            )
            return

        save_qr_settings(
            prefix=prefix,
            counter=max(1, counter),
            model_type=self.model_type
        )

        if callable(self.callback):
            self.callback()

        self.accept()
