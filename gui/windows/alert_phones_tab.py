# gui/windows/alert_phones_tab.py

import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox, QLineEdit, QFormLayout, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt

from backend.models_dao import get_models

# ✅ CORRECT DAO IMPORTS (MATCH YOUR BACKEND FILE EXACTLY)
from backend.alert_phones_dao import (
    get_phones_by_model_id,
    add_phone,
    update_phone,
    delete_phone
)


# -----------------------------------------------------
# Edit/Add Phone Dialog
# -----------------------------------------------------
class PhoneEditDialog(QDialog):
    def __init__(self, parent=None, phone=None):
        super().__init__(parent)
        self.phone = phone
        self.setWindowTitle("Edit Phone" if phone else "Add Phone Number")
        self.setModal(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.phone_input = QLineEdit()
        if self.phone:
            self.phone_input.setText(self.phone["phone_number"])

        self.phone_input.setPlaceholderText("+919876543210")
        form.addRow("Phone Number:", self.phone_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_cleaned_phone(self):
        text = self.phone_input.text().strip()
        cleaned = re.sub(r"[^0-9+]", "", text)
        if not cleaned:
            return None

        if not re.match(r"^\+\d{8,15}$", cleaned) and not re.match(r"^\d{10,15}$", cleaned):
            return None

        return cleaned if cleaned.startswith("+") else "+" + cleaned


# -----------------------------------------------------
# Alert Phones Tab
# -----------------------------------------------------
class AlertPhonesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_model_id = None
        self.phones = []
        self.setup_ui()
        self.load_models_combo()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2 style='color:#1e293b; margin:0;'>Alert Phone Numbers</h2>"))
        layout.addLayout(header)

        # Model selector
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Select Model:"))
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        layout.addLayout(model_layout)

        # Phone form
        phone_form = QHBoxLayout()
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+919876543210")
        self.phone_input.returnPressed.connect(self.add_or_update_phone)

        self.add_btn = QPushButton("Add Phone")
        self.add_btn.setStyleSheet("background:#10b981; color:white; padding:8px 16px; border-radius:8px;")
        self.add_btn.clicked.connect(self.add_or_update_phone)

        phone_form.addWidget(self.phone_input)
        phone_form.addWidget(self.add_btn)
        layout.addLayout(phone_form)

        # Error label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color:#dc2626; font-weight:600;")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Phone Number", "Actions"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Status
        self.status_label = QLabel("Select a model to manage alert phones")
        self.status_label.setStyleSheet("color:#64748b; font-style:italic;")
        layout.addWidget(self.status_label)
        layout.addStretch()

    # -------------------------------------------------
    def load_models_combo(self):
        self.model_combo.clear()
        self.model_combo.addItem("— Select a model —", None)
        models = get_models()
        for m in models:
            self.model_combo.addItem(m["name"], m["id"])

    # -------------------------------------------------
    def on_model_changed(self, index):
        self.current_model_id = self.model_combo.currentData()
        self.phone_input.clear()
        self.error_label.clear()

        if not self.current_model_id:
            self.phones = []
            self.table.setRowCount(0)
            self.status_label.setText("Select a model to manage alert phones")
            self.add_btn.setText("Add Phone")
            return

        self.status_label.setText("")
        self.load_phones()

    # -------------------------------------------------
    def load_phones(self):
        if not self.current_model_id:
            return

        self.phones = get_phones_by_model_id(self.current_model_id)
        self.table.setRowCount(len(self.phones))

        for i, phone in enumerate(self.phones):
            self.table.setItem(i, 0, QTableWidgetItem(phone["phone_number"]))

            actions = QWidget()
            hlay = QHBoxLayout(actions)
            hlay.setContentsMargins(5, 5, 5, 5)

            edit_btn = QPushButton("Edit")
            edit_btn.setStyleSheet("background:#3b82f6; color:white; padding:5px 10px; border-radius:6px;")
            edit_btn.clicked.connect(lambda _, p=phone: self.edit_phone(p))

            delete_btn = QPushButton("Delete")
            delete_btn.setStyleSheet("background:#ef4444; color:white; padding:5px 10px; border-radius:6px;")
            delete_btn.clicked.connect(lambda _, pid=phone["id"]: self.delete_phone(pid))

            hlay.addWidget(edit_btn)
            hlay.addWidget(delete_btn)
            self.table.setCellWidget(i, 1, actions)

    # -------------------------------------------------
    def validate_phone(self, number):
        cleaned = re.sub(r"[^0-9+]", "", number.strip())
        if not cleaned:
            return None, "Phone number is required"

        if not re.match(r"^\+\d{8,15}$", cleaned) and not re.match(r"^\d{10,15}$", cleaned):
            return None, "Invalid format. Use +919876543210"

        cleaned = cleaned if cleaned.startswith("+") else "+" + cleaned

        if any(p["phone_number"] == cleaned and p["id"] != getattr(self, "editing_phone_id", None) for p in self.phones):
            return None, "This phone number is already added"

        return cleaned, ""

    # -------------------------------------------------
    def add_or_update_phone(self):
        if not self.current_model_id:
            self.error_label.setText("Please select a model first")
            return

        raw = self.phone_input.text()
        cleaned, error = self.validate_phone(raw)

        if not cleaned:
            self.error_label.setText(error)
            return

        try:
            if hasattr(self, "editing_phone_id"):
                update_phone(self.editing_phone_id, cleaned)
                QMessageBox.information(self, "Success", "Phone number updated")
                del self.editing_phone_id
                self.add_btn.setText("Add Phone")
            else:
                add_phone(self.current_model_id, cleaned)
                QMessageBox.information(self, "Success", "Phone number added")

            self.phone_input.clear()
            self.error_label.clear()
            self.load_phones()

        except Exception as e:
            self.error_label.setText(str(e))

    # -------------------------------------------------
    def edit_phone(self, phone):
        self.editing_phone_id = phone["id"]
        self.phone_input.setText(phone["phone_number"])
        self.phone_input.setFocus()
        self.add_btn.setText("Update Phone")
        self.error_label.clear()

    # -------------------------------------------------
    def delete_phone(self, phone_id):
        reply = QMessageBox.question(self, "Confirm", "Remove this phone number?")
        if reply == QMessageBox.StandardButton.Yes:
            delete_phone(phone_id)
            self.load_phones()

    # -------------------------------------------------
    # ✅ REQUIRED BY SettingsWindow
    # -------------------------------------------------
    def get_all_phone_records(self):
        return list(self.phones) if hasattr(self, "phones") else []
