from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDialogButtonBox, QMessageBox,
    QComboBox, QLabel
)
from PySide6.QtCore import Qt

from backend.models_dao import add_model, update_model


class ModelEditDialog(QDialog):
    """
    Model Add / Edit Dialog – Production Safe

    Purpose:
    - Add a new model
    - Edit existing model parameters

    Styling:
    - styles/dialogs.qss
    """

    WIDTH = 420
    HEIGHT = 260

    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model

        self.setObjectName("ModelEditDialog")
        self.setWindowTitle("Edit Model" if model else "Add New Model")
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()

    # ---------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -------------------------------------------------
        # Title
        # -------------------------------------------------
        title = QLabel(
            "Edit Model" if self.model else "Add New Model"
        )
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # -------------------------------------------------
        # Form
        # -------------------------------------------------
        form = QFormLayout()
        form.setSpacing(12)

        # -------------------------------
        # Model Name
        # -------------------------------
        self.name_edit = QLineEdit(
            self.model.get("name", "") if self.model else ""
        )
        self.name_edit.setObjectName("ModelNameInput")
        form.addRow("Model Name:", self.name_edit)

        # -------------------------------
        # Model Type
        # -------------------------------
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("ModelTypeCombo")
        self.type_combo.addItems(["RHD", "LHD"])

        if self.model:
            model_type = self.model.get("model_type", "RHD")
            index = self.type_combo.findText(model_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        form.addRow("Model Type:", self.type_combo)

        # -------------------------------
        # Limits
        # -------------------------------
        self.lower_edit = QLineEdit(
            str(self.model.get("lower_limit", "")) if self.model else ""
        )
        self.upper_edit = QLineEdit(
            str(self.model.get("upper_limit", "")) if self.model else ""
        )

        self.lower_edit.setObjectName("LowerLimitInput")
        self.upper_edit.setObjectName("UpperLimitInput")

        self.lower_edit.setPlaceholderText("e.g. 49.95")
        self.upper_edit.setPlaceholderText("e.g. 52.30")

        form.addRow("Lower Limit (mm):", self.lower_edit)
        form.addRow("Upper Limit (mm):", self.upper_edit)

        layout.addLayout(form)

        # -------------------------------------------------
        # Buttons
        # -------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.setObjectName("DialogButtons")

        ok_btn = buttons.button(QDialogButtonBox.Ok)
        ok_btn.setText("Save")
        ok_btn.setProperty("role", "primary")

        cancel_btn = buttons.button(QDialogButtonBox.Cancel)
        cancel_btn.setProperty("role", "secondary")

        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    # ---------------------------------------------------
    def _on_accept(self):
        name = self.name_edit.text().strip()
        model_type = self.type_combo.currentText()

        # -------------------------------
        # Validation
        # -------------------------------
        if not name:
            QMessageBox.critical(
                self, "Validation Error", "Model name is required."
            )
            return

        try:
            lower = float(self.lower_edit.text())
            upper = float(self.upper_edit.text())
        except ValueError:
            QMessageBox.critical(
                self, "Validation Error", "Limits must be valid numbers."
            )
            return

        if lower >= upper:
            QMessageBox.critical(
                self,
                "Validation Error",
                "Lower limit must be less than upper limit."
            )
            return

        # -------------------------------
        # Persist
        # -------------------------------
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
        except Exception as e:
            QMessageBox.critical(self, "Database Error", str(e))
            return

        self.accept()
