# gui/windows/qr_settings_modal.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QLabel, QDialogButtonBox,
    QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.settings_dao import get_qr_settings, save_qr_settings
from gui.styles.app_styles import apply_base_dialog_style


class QRSettingsModal(QDialog):
    """
    QR Settings Modal – Production Safe

    Purpose:
    - Configure QR prefix & counter
    - Preview next QR code
    - Model type is READ-ONLY (comes from model)

    Styling:
    - Internal (apply_base_dialog_style)
    """

    WIDTH = 480
    HEIGHT = 380

    # --------------------------------------------------
    def __init__(self, parent=None, model=None, callback=None):
        super().__init__(parent)

        self.model = model or {}
        self.callback = callback

        self.setObjectName("QRSettingsModal")
        self.setWindowTitle("QR Code Settings")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._load_settings()
        self._build_ui()

        # Apply shared internal styling
        apply_base_dialog_style(self)

    # --------------------------------------------------
    # Data
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
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(22)

        # ---------------- Title ----------------
        title = QLabel(
            f"QR Settings – {self.model.get('name', '')}"
        )
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        subtitle = QLabel(f"Model Type: {self.model_type}")
        subtitle.setObjectName("MutedText")
        subtitle.setAlignment(Qt.AlignCenter)

        root.addWidget(title)
        root.addWidget(subtitle)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.prefix_edit.setPlaceholderText("QR text prefix (e.g. G510)")

        self.counter_edit = QLineEdit(str(self.qr_counter))
        self.counter_edit.setPlaceholderText("Starting counter")
        self.counter_edit.setMaximumWidth(180)

        form.addRow("QR Text Prefix:", self.prefix_edit)
        form.addRow("Starting Counter:", self.counter_edit)

        root.addLayout(form)

        # ---------------- Preview ----------------
        preview_title = QLabel("Next QR Code Preview")
        preview_title.setObjectName("SectionTitle")
        preview_title.setAlignment(Qt.AlignCenter)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self.preview_label.setObjectName("QrPreview")

        root.addWidget(preview_title)
        root.addWidget(self.preview_label)

        self.prefix_edit.textChanged.connect(self._update_preview)
        self.counter_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        # ---------------- Buttons ----------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Save & Apply")
        ok_btn.setProperty("role", "primary")

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setProperty("role", "secondary")

        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)

        root.addStretch()
        root.addWidget(buttons)

    # --------------------------------------------------
    # Logic
    # --------------------------------------------------
    def _update_preview(self):
        prefix = self.prefix_edit.text().strip() or "Text"

        try:
            counter = int(self.counter_edit.text())
        except ValueError:
            counter = 1

        self.preview_label.setText(
            f"{prefix}.{str(counter).zfill(5)}"
        )

    # --------------------------------------------------
    def _save(self):
        prefix = self.prefix_edit.text().strip()

        if not prefix:
            QMessageBox.warning(
                self,
                "Invalid Prefix",
                "QR text prefix cannot be empty."
            )
            self.prefix_edit.setFocus()
            return

        try:
            counter = int(self.counter_edit.text())
        except ValueError:
            QMessageBox.warning(
                self,
                "Invalid Counter",
                "Starting counter must be a valid number."
            )
            self.counter_edit.setFocus()
            return

        save_qr_settings(
            prefix=prefix,
            counter=max(1, counter),
            model_type=self.model_type
        )

        if callable(self.callback):
            self.callback()

        self.accept()