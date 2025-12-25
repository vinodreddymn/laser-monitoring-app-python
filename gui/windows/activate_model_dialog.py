from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QLabel, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt

from backend.settings_dao import get_settings, save_settings
from backend.models_dao import set_active_model


class ActivateModelDialog(QDialog):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model

        self.setWindowTitle(f"Activate Model: {model['name']}")
        self.resize(500, 400)

        self.load_settings()
        self.setup_ui()

    # --------------------------------------------------
    def load_settings(self):
        s = get_settings()
        self.qr_prefix = s.get("qr_text_prefix", "Part")
        self.qr_counter = s.get("qr_start_counter", 1)
        self.model_type = self.model.get("model_type", "RHD")

    # --------------------------------------------------
    def save_qr_settings(self):
        save_settings({
            "qr_text_prefix": self.qr_prefix.strip(),
            "qr_start_counter": max(1, int(self.qr_counter)),
            "model_type": self.model_type
        })

    # --------------------------------------------------
    def get_next_qr(self):
        prefix = self.qr_prefix.strip() or "Text"
        return f"{prefix}.{str(self.qr_counter).zfill(5)}"

    # --------------------------------------------------
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        layout.addWidget(
            QLabel(f"<h3>Activate Model: <b>{self.model['name']}</b> ({self.model_type})</h3>")
        )

        form = QFormLayout()
        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.counter_edit = QLineEdit(str(self.qr_counter))
        self.counter_edit.setMaximumWidth(120)

        form.addRow("QR Text Prefix:", self.prefix_edit)
        form.addRow("Starting Counter:", self.counter_edit)
        layout.addLayout(form)

        preview = QLabel()
        preview.setAlignment(Qt.AlignCenter)
        preview.setStyleSheet("""
            background:#ecfdf5;
            padding:20px;
            border:2px dashed #10b981;
            border-radius:12px;
            margin:20px 0;
            font-family:Consolas;
            font-size:22px;
            color:#065f46;
        """)
        layout.addWidget(preview)

        def update_preview():
            self.qr_prefix = self.prefix_edit.text()
            try:
                self.qr_counter = int(self.counter_edit.text())
            except:
                self.qr_counter = 1
            preview.setText(f"Next QR Code: <b>{self.get_next_qr()}</b>")

        self.prefix_edit.textChanged.connect(update_preview)
        self.counter_edit.textChanged.connect(update_preview)
        update_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText("Activate & Save")
        buttons.accepted.connect(self.activate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # --------------------------------------------------
    def activate(self):
        # 1️⃣ Save QR settings (merge-safe)
        self.save_qr_settings()

        # 2️⃣ Save active model to DB (ONLY place)
        set_active_model(self.model["id"])

        QMessageBox.information(
            self,
            "Success",
            f"Activated: {self.model['name']}\nNext QR: {self.get_next_qr()}"
        )
        super().accept()
