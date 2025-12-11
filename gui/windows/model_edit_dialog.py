# gui/model_edit_dialog.py
from PySide6.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox, QMessageBox
from backend.models_dao import add_model, update_model


class ModelEditDialog(QDialog):
    def __init__(self, parent=None, model=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Edit Model" if model else "Add New Model")
        self.resize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.name_edit = QLineEdit(self.model["name"] if self.model else "")
        self.lower_edit = QLineEdit(str(self.model["lower_limit"]) if self.model else "")
        self.upper_edit = QLineEdit(str(self.model["upper_limit"]) if self.model else "")

        for edit in (self.lower_edit, self.upper_edit):
            edit.setPlaceholderText("e.g. 49.95")

        form.addRow("Model Name:", self.name_edit)
        form.addRow("Lower Limit (mm):", self.lower_edit)
        form.addRow("Upper Limit (mm):", self.upper_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def accept(self):
        name = self.name_edit.text().strip()
        try:
            lower = float(self.lower_edit.text())
            upper = float(self.upper_edit.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Limits must be valid numbers")
            return

        if not name:
            QMessageBox.critical(self, "Error", "Model name is required")
        elif lower >= upper:
            QMessageBox.critical(self, "Error", "Lower limit must be less than upper limit")
        else:
            if self.model:
                update_model(self.model["id"], name, lower, upper)
            else:
                add_model(name, lower, upper)
            super().accept()