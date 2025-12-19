import re
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox, QLineEdit, QFormLayout, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt

from backend.models_dao import get_models
from backend.alert_phones_dao import (
    get_phones_by_model_id,
    add_phone,
    update_phone,
    delete_phone
)


# -----------------------------------------------------
# Add / Edit Contact Dialog (Name + Phone)
# -----------------------------------------------------
class PhoneEditDialog(QDialog):
    def __init__(self, parent=None, contact=None):
        super().__init__(parent)
        self.contact = contact
        self.setWindowTitle("Edit Contact" if contact else "Add Alert Contact")
        self.setModal(True)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.name_input.setPlaceholderText("Person Name")
        self.phone_input.setPlaceholderText("+919876543210")

        if self.contact:
            self.name_input.setText(self.contact.get("name", ""))
            self.phone_input.setText(self.contact.get("phone_number", ""))

        form.addRow("Name:", self.name_input)
        form.addRow("Phone Number:", self.phone_input)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)

    def get_data(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()

        phone = re.sub(r"[^0-9+]", "", phone)
        if phone and not phone.startswith("+"):
            phone = "+" + phone

        if not name:
            return None, None, "Name is required"

        if not phone or not re.match(r"^\+\d{8,15}$", phone):
            return None, None, "Invalid phone number format"

        return name, phone, None


# -----------------------------------------------------
# Alert Phones Tab
# -----------------------------------------------------
class AlertPhonesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_model_id = None
        self.contacts = []
        self._build_ui()
        self._load_models()

    # -------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        layout.addWidget(
            QLabel("<h2 style='margin:0;'>Alert Contacts</h2>")
        )

        # Model selector
        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Model:"))

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(300)
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        model_row.addWidget(self.model_combo)
        model_row.addStretch()
        layout.addLayout(model_row)

        # Add button
        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Contact")
        self.add_btn.clicked.connect(self._add_contact)
        btn_row.addWidget(self.add_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # Table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(
            ["Name", "Phone Number", "Actions"]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(self.table)

        # Status
        self.status_label = QLabel("Select a model to manage alert contacts")
        self.status_label.setStyleSheet("color:#64748b; font-style:italic;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    # -------------------------------------------------
    def _load_models(self):
        self.model_combo.clear()
        self.model_combo.addItem("— Select a model —", None)

        for m in get_models():
            self.model_combo.addItem(m["name"], m["id"])

    # -------------------------------------------------
    def _on_model_changed(self):
        self.current_model_id = self.model_combo.currentData()

        if not self.current_model_id:
            self.contacts = []
            self.table.setRowCount(0)
            self.status_label.setText("Select a model to manage alert contacts")
            return

        self.status_label.setText("")
        self._load_contacts()

    # -------------------------------------------------
    def _load_contacts(self):
        self.contacts = get_phones_by_model_id(self.current_model_id)
        self.table.setRowCount(len(self.contacts))

        for row, c in enumerate(self.contacts):
            self.table.setItem(row, 0, QTableWidgetItem(c.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(c["phone_number"]))

            actions = QWidget()
            hlay = QHBoxLayout(actions)
            hlay.setContentsMargins(0, 0, 0, 0)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(
                lambda _, contact=c: self._edit_contact(contact)
            )

            del_btn = QPushButton("Delete")
            del_btn.clicked.connect(
                lambda _, cid=c["id"]: self._delete_contact(cid)
            )

            hlay.addWidget(edit_btn)
            hlay.addWidget(del_btn)

            self.table.setCellWidget(row, 2, actions)

    # -------------------------------------------------
    def _add_contact(self):
        if not self.current_model_id:
            QMessageBox.warning(self, "Select Model", "Please select a model first")
            return

        dlg = PhoneEditDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        name, phone, error = dlg.get_data()
        if error:
            QMessageBox.warning(self, "Invalid Data", error)
            return

        add_phone(self.current_model_id, name, phone)
        self._load_contacts()

    # -------------------------------------------------
    def _edit_contact(self, contact):
        dlg = PhoneEditDialog(self, contact)
        if dlg.exec() != QDialog.Accepted:
            return

        name, phone, error = dlg.get_data()
        if error:
            QMessageBox.warning(self, "Invalid Data", error)
            return

        update_phone(contact["id"], name, phone)
        self._load_contacts()

    # -------------------------------------------------
    def _delete_contact(self, contact_id):
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Remove this alert contact?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            delete_phone(contact_id)
            self._load_contacts()

    # -------------------------------------------------
    # Required by SettingsWindow
    # -------------------------------------------------
    def get_all_phone_records(self):
        return list(self.contacts)
