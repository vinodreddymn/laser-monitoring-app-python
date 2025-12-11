# gui/activate_model_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QLabel, QDialogButtonBox, QMessageBox
from PySide6.QtCore import Qt
import json
import os


SETTINGS_FILE = "settings.json"


class ActivateModelDialog(QDialog):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle(f"Activate Model: {model['name']}")
        self.resize(500, 400)
        self.load_settings()
        self.setup_ui()

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                s = json.load(f)
                self.qr_prefix = s.get("qr_text_prefix", "Part")
                self.qr_counter = s.get("qr_start_counter", 1)
        else:
            self.qr_prefix = "Part"
            self.qr_counter = 1

    def save_settings(self):
        data = {
            "qr_text_prefix": self.qr_prefix.strip(),
            "qr_start_counter": max(1, int(self.qr_counter))
        }
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)

    def get_next_qr(self):
        prefix = self.qr_prefix.strip() or "Text"
        return f"{prefix}-{str(self.qr_counter).zfill(5)}"

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        layout.addWidget(QLabel(f"<h3>Activate Model: <b>{self.model['name']}</b></h3>"))

        form = QFormLayout()
        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.counter_edit = QLineEdit(str(self.qr_counter))
        self.counter_edit.setMaximumWidth(100)

        form.addRow("QR Text Prefix:", self.prefix_edit)
        form.addRow("Starting Counter:", self.counter_edit)
        layout.addLayout(form)

        preview = QLabel(f"Next QR Code: <b style='font-size:24px; color:#065f46; font-family:Consolas'>{self.get_next_qr()}</b>")
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview.setStyleSheet("""
            background:#ecfdf5; padding:20px; border:2px dashed #10b981;
            border-radius:12px; margin:20px 0;
        """)
        layout.addWidget(preview)

        def update_preview():
            self.qr_prefix = self.prefix_edit.text()
            try:
                self.qr_counter = int(self.counter_edit.text() or 1)
            except:
                self.qr_counter = 1
            preview.setText(f"Next QR Code: <b style='font-size:24px; color:#065f46; font-family:Consolas'>{self.get_next_qr()}</b>")

        self.prefix_edit.textChanged.connect(update_preview)
        self.counter_edit.textChanged.connect(update_preview)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Activate & Save")
        buttons.accepted.connect(self.activate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def activate(self):
        self.save_settings()
        # Save active model (you can extend this)
        with open(SETTINGS_FILE, "r+") as f:
            data = json.load(f)
            data["active_model_id"] = self.model["id"]
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()

        QMessageBox.information(self, "Success", f"Activated: {self.model['name']}\nNext QR: {self.get_next_qr()}")
        super().accept()