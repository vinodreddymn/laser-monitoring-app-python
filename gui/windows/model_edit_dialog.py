# gui/windows/model_edit_dialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout,
    QLineEdit, QDialogButtonBox, QMessageBox,
    QComboBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.models_dao import add_model, update_model
from gui.styles.app_styles import apply_base_dialog_style


class ModelEditDialog(QDialog):
    """
    Model Add / Edit Dialog – Production Safe

    Purpose:
    - Add a new QC model
    - Edit existing model parameters

    Styling:
    - Internal (apply_base_dialog_style)
    """

    WIDTH = 440
    HEIGHT = 300

    # ---------------------------------------------------
    def __init__(self, parent=None, model=None):
        super().__init__(parent)

        self.model = model

        self.setObjectName("ModelEditDialog")
        self.setWindowTitle("Edit Model" if model else "Add New Model")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()

        # Apply shared styling
        apply_base_dialog_style(self)

    # ---------------------------------------------------
    # UI
    # ---------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        # ---------------- Title ----------------
        title = QLabel(
            "Edit Model" if self.model else "Add New Model"
        )
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))

        root.addWidget(title)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(14)
        form.setLabelAlignment(Qt.AlignRight)

        # ---------------- Model Name ----------------
        self.name_edit = QLineEdit(
            self.model.get("name", "") if self.model else ""
        )
        self.name_edit.setPlaceholderText("Model name (e.g. G510)")
        self.name_edit.setObjectName("ModelNameInput")
        self.name_edit.setFocus()

        form.addRow("Model Name:", self.name_edit)

        # ---------------- Model Type ----------------
        self.type_combo = QComboBox()
        self.type_combo.setObjectName("ModelTypeCombo")
        self.type_combo.addItems(["RHD", "LHD"])

        if self.model:
            model_type = self.model.get("model_type", "RHD")
            index = self.type_combo.findText(model_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        form.addRow("Model Type:", self.type_combo)

        # ---------------- Limits ----------------
        self.lower_edit = QLineEdit(
            str(self.model.get("lower_limit", "")) if self.model else ""
        )
        self.upper_edit = QLineEdit(
            str(self.model.get("upper_limit", "")) if self.model else ""
        )

        self.lower_edit.setPlaceholderText("Lower limit (mm)")
        self.upper_edit.setPlaceholderText("Upper limit (mm)")

        self.lower_edit.setObjectName("LowerLimitInput")
        self.upper_edit.setObjectName("UpperLimitInput")

        form.addRow("Lower Limit (mm):", self.lower_edit)
        form.addRow("Upper Limit (mm):", self.upper_edit)

        root.addLayout(form)

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

        root.addStretch()
        root.addWidget(buttons)

    # ---------------------------------------------------
    # Logic
    # ---------------------------------------------------
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
                "Limits must be valid numbers."
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
