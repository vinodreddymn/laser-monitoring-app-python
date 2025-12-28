# gui/windows/activate_model_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.settings_dao import get_settings, save_settings
from backend.models_dao import set_active_model
from gui.styles.app_styles import apply_base_dialog_style


class ActivateModelDialog(QDialog):
    """
    Activate Model Dialog – Production Safe

    Purpose:
    - Activate selected model
    - Configure QR prefix & counter

    Styling:
    - Internal (apply_base_dialog_style)
    """

    WIDTH = 520
    HEIGHT = 420

    # --------------------------------------------------
    def __init__(self, parent=None, model=None):
        super().__init__(parent)

        self.model = model or {}

        self.setObjectName("ActivateModelDialog")
        self.setWindowTitle("Activate Model")
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setModal(True)

        self._load_settings()
        self._build_ui()

        # Apply shared styling
        apply_base_dialog_style(self)

    # --------------------------------------------------
    def _load_settings(self):
        s = get_settings() or {}
        self.qr_prefix = s.get("qr_text_prefix", "Part")
        self.qr_counter = int(s.get("qr_start_counter", 1))
        self.model_type = self.model.get("model_type", "RHD")

    # --------------------------------------------------
    def _save_qr_settings(self):
        save_settings({
            "qr_text_prefix": self.qr_prefix.strip(),
            "qr_start_counter": max(1, int(self.qr_counter)),
            "model_type": self.model_type,
        })

    # --------------------------------------------------
    def _get_next_qr(self) -> str:
        prefix = self.qr_prefix.strip() or "Text"
        return f"{prefix}.{str(self.qr_counter).zfill(5)}"

    # --------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        # --------------------------------------------------
        # Header / Title
        # --------------------------------------------------
        title = QLabel(
            f"Activate Model: <b>{self.model.get('name', 'Unknown')}</b>"
        )
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        subtitle = QLabel(f"Model Type: {self.model_type}")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setObjectName("MutedText")

        root.addWidget(title)
        root.addWidget(subtitle)

        # --------------------------------------------------
        # Form Section
        # --------------------------------------------------
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.prefix_edit.setPlaceholderText("QR prefix (e.g. G510)")
        self.prefix_edit.setObjectName("QrPrefixInput")

        self.counter_edit = QLineEdit(str(self.qr_counter))
        self.counter_edit.setPlaceholderText("Starting number")
        self.counter_edit.setMaximumWidth(160)
        self.counter_edit.setObjectName("QrCounterInput")

        form.addRow("QR Text Prefix:", self.prefix_edit)
        form.addRow("Starting Counter:", self.counter_edit)

        root.addLayout(form)

        # --------------------------------------------------
        # Preview Section
        # --------------------------------------------------
        preview_title = QLabel("Next QR Code Preview")
        preview_title.setObjectName("SectionTitle")
        preview_title.setAlignment(Qt.AlignCenter)

        self.preview_lbl = QLabel()
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        self.preview_lbl.setFont(QFont("Consolas", 20, QFont.Weight.Bold))
        self.preview_lbl.setObjectName("QrPreview")

        root.addWidget(preview_title)
        root.addWidget(self.preview_lbl)

        self.prefix_edit.textChanged.connect(self._update_preview)
        self.counter_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        # --------------------------------------------------
        # Action Buttons
        # --------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.setObjectName("DialogButtons")

        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Activate & Save")
        ok_btn.setProperty("role", "primary")

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setProperty("role", "secondary")

        buttons.accepted.connect(self._activate)
        buttons.rejected.connect(self.reject)

        root.addStretch()
        root.addWidget(buttons)

    # --------------------------------------------------
    def _update_preview(self):
        self.qr_prefix = self.prefix_edit.text().strip()

        try:
            self.qr_counter = int(self.counter_edit.text())
        except ValueError:
            self.qr_counter = 1

        self.preview_lbl.setText(
            f"{self._get_next_qr()}"
        )

    # --------------------------------------------------
    def _activate(self):
        # Basic validation
        if not self.prefix_edit.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Prefix",
                "QR text prefix cannot be empty."
            )
            self.prefix_edit.setFocus()
            return

        # 1️⃣ Save QR settings
        self._save_qr_settings()

        # 2️⃣ Activate model (single source of truth)
        set_active_model(self.model.get("id"))

        QMessageBox.information(
            self,
            "Model Activated",
            f"Model: {self.model.get('name')}\n"
            f"Next QR: {self._get_next_qr()}"
        )
        self.accept()