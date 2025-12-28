from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt

from backend.settings_dao import get_settings, save_settings
from backend.models_dao import set_active_model


class ActivateModelDialog(QDialog):
    """
    Activate Model Dialog – Production Safe

    Purpose:
    - Activate selected model
    - Configure QR prefix & counter

    Styling:
    - styles/dialogs.qss
    """

    WIDTH = 500
    HEIGHT = 400

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model or {}

        self.setObjectName("ActivateModelDialog")
        self.setWindowTitle(f"Activate Model: {self.model.get('name', 'Unknown')}")
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._load_settings()
        self._build_ui()

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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # --------------------------------------------------
        # Title
        # --------------------------------------------------
        title = QLabel(
            f"Activate Model: <b>{self.model.get('name', 'Unknown')}</b> "
            f"[{self.model_type}]"
        )
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # --------------------------------------------------
        # Form
        # --------------------------------------------------
        form = QFormLayout()
        form.setSpacing(12)

        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.prefix_edit.setObjectName("QrPrefixInput")

        self.counter_edit = QLineEdit(str(self.qr_counter))
        self.counter_edit.setObjectName("QrCounterInput")
        self.counter_edit.setMaximumWidth(140)

        form.addRow("QR Text Prefix:", self.prefix_edit)
        form.addRow("Starting Counter:", self.counter_edit)

        layout.addLayout(form)

        # --------------------------------------------------
        # Preview
        # --------------------------------------------------
        self.preview_lbl = QLabel()
        self.preview_lbl.setObjectName("QrPreview")
        self.preview_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview_lbl)

        self.prefix_edit.textChanged.connect(self._update_preview)
        self.counter_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        # --------------------------------------------------
        # Buttons
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

        layout.addWidget(buttons)

    # --------------------------------------------------
    def _update_preview(self):
        self.qr_prefix = self.prefix_edit.text().strip()

        try:
            self.qr_counter = int(self.counter_edit.text())
        except ValueError:
            self.qr_counter = 1

        self.preview_lbl.setText(
            f"Next QR Code: <b>{self._get_next_qr()}</b>"
        )

    # --------------------------------------------------
    def _activate(self):
        # 1️⃣ Save QR settings
        self._save_qr_settings()

        # 2️⃣ Activate model (single source of truth)
        set_active_model(self.model.get("id"))

        QMessageBox.information(
            self,
            "Model Activated",
            f"Activated: {self.model.get('name')}\n"
            f"Next QR: {self._get_next_qr()}"
        )
        self.accept()
