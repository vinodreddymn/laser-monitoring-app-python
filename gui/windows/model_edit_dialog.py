from typing import Optional, Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
    QMessageBox,
    QComboBox,
    QLabel,
    QFrame
)
from PySide6.QtCore import Qt

from backend.models_dao import add_model, update_model
from gui.styles.app_styles import apply_base_dialog_style


class ModelEditDialog(QDialog):
    """
    Model Add / Edit Dialog – Factory Safe

    Purpose
    -------
    • Create new QC model
    • Edit existing model parameters
    • Supervisor-only configuration

    Design
    ------
    • Fixed size
    • Clear validation
    • Stable UI (no hover)
    """

    WIDTH = 800
    HEIGHT = 660

    # --------------------------------------------------
    def __init__(self, parent=None, model: Optional[Dict] = None):
        super().__init__(parent)

        self.model = model

        self.setObjectName("ModelEditDialog")
        self.setWindowTitle("Edit Model" if model else "Add New Model")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()
        apply_base_dialog_style(self)

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 24)
        root.setSpacing(22)

        # ---------------- Header ----------------
        title = QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)

        root.addWidget(title)

        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        root.addWidget(divider)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignRight)

        # Model Name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Model name (e.g. G510)")
        self.name_edit.setFocus()

        # Model Type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["RHD", "LHD"])

        # Limits
        self.lower_edit = QLineEdit()
        self.upper_edit = QLineEdit()

        self.lower_edit.setPlaceholderText("Lower limit (mm)")
        self.upper_edit.setPlaceholderText("Upper limit (mm)")

        # Populate if editing
        if self.model:
            self.name_edit.setText(self.model.get("name", ""))

            model_type = self.model.get("model_type", "RHD")
            index = self.type_combo.findText(model_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

            self.lower_edit.setText(str(self.model.get("lower_limit", "")))
            self.upper_edit.setText(str(self.model.get("upper_limit", "")))

        form.addRow("Model Name", self.name_edit)
        form.addRow("Model Type", self.type_combo)
        form.addRow("Lower Limit (mm)", self.lower_edit)
        form.addRow("Upper Limit (mm)", self.upper_edit)

        root.addLayout(form)
        root.addStretch()

        # ---------------- Buttons ----------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Save")
        ok_btn.setProperty("role", "primary")

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setProperty("role", "secondary")

        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        root.addWidget(buttons)

    # ==================================================
    # LOGIC
    # ==================================================
    def _on_accept(self):
        name = self.name_edit.text().strip()
        model_type = self.type_combo.currentText()

        # ---------------- Validation ----------------
        if not name:
            QMessageBox.critical(
                self,
                "Validation Error",
                "Model name is required."
            )
            self.name_edit.setFocus()
            return

        try:
            lower = float(self.lower_edit.text())
            upper = float(self.upper_edit.text())
        except ValueError:
            QMessageBox.critical(
                self,
                "Validation Error",
                "Lower and upper limits must be valid numbers."
            )
            return

        if lower >= upper:
            QMessageBox.critical(
                self,
                "Validation Error",
                "Lower limit must be less than upper limit."
            )
            return

        # ---------------- Persist ----------------
        try:
            if self.model:
                update_model(
                    self.model["id"],
                    name,
                    model_type,
                    lower,
                    upper
                )
            else:
                add_model(
                    name,
                    model_type,
                    lower,
                    upper
                )
        except Exception as exc:
            QMessageBox.critical(
                self,
                "Database Error",
                str(exc)
            )
            return

        self.accept()
