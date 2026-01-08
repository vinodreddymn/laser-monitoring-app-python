from typing import Optional, Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QMessageBox,
    QFrame
)
from PySide6.QtCore import Qt

from backend.settings_dao import get_settings, save_settings
from backend.models_dao import set_active_model
from gui.styles.app_styles import apply_base_dialog_style


class ActivateModelDialog(QDialog):
    """
    Activate Model – Factory Floor Safe (Final)

    ✔ Stable layout
    ✔ Clear QR preview
    ✔ Explicit buttons (no QDialogButtonBox)
    ✔ No hover reliance
    ✔ No clipping / padding issues
    """

    WIDTH = 900
    HEIGHT = 700

    # --------------------------------------------------
    def __init__(self, parent=None, model: Optional[Dict] = None):
        super().__init__(parent)

        self.model = model or {}

        self.setObjectName("ActivateModelDialog")
        self.setWindowTitle("Activate Model")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._load_settings()
        self._build_ui()

        apply_base_dialog_style(self)

    # ==================================================
    # SETTINGS
    # ==================================================
    def _load_settings(self):
        settings = get_settings() or {}

        self.qr_prefix: str = settings.get("qr_text_prefix", "Part")
        self.qr_counter: int = int(settings.get("qr_start_counter", 1))
        self.model_type: str = self.model.get("model_type", "RHD")

    def _save_qr_settings(self):
        save_settings({
            "qr_text_prefix": self.qr_prefix.strip(),
            "qr_start_counter": max(1, int(self.qr_counter)),
            "model_type": self.model_type
        })

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # ---------------- Title ----------------
        title = QLabel(f"Activate Model: {self.model.get('name', 'Unknown')}")
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel(f"Model Type: {self.model_type}")
        subtitle.setObjectName("MutedText")
        subtitle.setAlignment(Qt.AlignCenter)

        root.addWidget(title)
        root.addWidget(subtitle)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        root.addWidget(divider)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        self.prefix_edit = QLineEdit(self.qr_prefix)
        self.prefix_edit.setPlaceholderText("QR prefix (e.g. G510)")
        self.prefix_edit.setMaximumWidth(300)

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

        self.preview_lbl = QLabel()
        self.preview_lbl.setObjectName("QrPreview")
        self.preview_lbl.setAlignment(Qt.AlignCenter)

        root.addWidget(preview_title)
        root.addWidget(self.preview_lbl)

        self.prefix_edit.textChanged.connect(self._update_preview)
        self.counter_edit.textChanged.connect(self._update_preview)
        self._update_preview()

        root.addStretch()

        # ---------------- Buttons ----------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        self.btn_activate = QPushButton("Activate & Save")
        self.btn_activate.setProperty("role", "primary")
        self.btn_activate.setMinimumWidth(180)
        self.btn_activate.clicked.connect(self._activate)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setProperty("role", "secondary")
        self.btn_cancel.setMinimumWidth(120)
        self.btn_cancel.clicked.connect(self.reject)

        btn_row.addStretch()
        btn_row.addWidget(self.btn_activate)
        btn_row.addWidget(self.btn_cancel)

        root.addLayout(btn_row)

    # ==================================================
    # LOGIC
    # ==================================================
    def _update_preview(self):
        self.qr_prefix = self.prefix_edit.text().strip()

        try:
            self.qr_counter = int(self.counter_edit.text())
        except ValueError:
            self.qr_counter = 1

        self.preview_lbl.setText(self._get_next_qr())

    def _get_next_qr(self) -> str:
        prefix = self.qr_prefix or "QR"
        return f"{prefix}.{str(max(1, self.qr_counter)).zfill(5)}"

    def _activate(self):
        if not self.prefix_edit.text().strip():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "QR text prefix cannot be empty."
            )
            self.prefix_edit.setFocus()
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Activation",
            f"Activate model '{self.model.get('name')}'?\n\n"
            f"Next QR:\n{self._get_next_qr()}",
            QMessageBox.Yes | QMessageBox.No
        )

        if confirm != QMessageBox.Yes:
            return

        # Save settings
        self._save_qr_settings()

        # Activate model
        set_active_model(self.model.get("id"))

        QMessageBox.information(
            self,
            "Model Activated",
            f"Model activated successfully.\n\n"
            f"Next QR Code:\n{self._get_next_qr()}"
        )

        self.accept()
