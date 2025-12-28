# gui/windows/alert_phones_tab.py

import re

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox, QLineEdit, QFormLayout, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from backend.models_dao import get_models
from backend.alert_phones_dao import (
    get_phones_by_model_id,
    add_phone,
    update_phone,
    delete_phone
)

from gui.styles.app_styles import apply_base_dialog_style


# =====================================================
# Phone Add / Edit Dialog
# =====================================================
class PhoneEditDialog(QDialog):
    """
    Alert Contact Dialog – Production Safe

    Purpose:
    - Add or edit alert contact
    - Validate phone number format

    Styling:
    - Internal (apply_base_dialog_style)
    """

    WIDTH = 380
    HEIGHT = 240

    def __init__(self, parent=None, contact=None):
        super().__init__(parent)

        self.contact = contact

        self.setObjectName("PhoneEditDialog")
        self.setWindowTitle(
            "Edit Alert Contact" if contact else "Add Alert Contact"
        )
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        self._build_ui()
        apply_base_dialog_style(self)

    # -------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # ---------------- Title ----------------
        title = QLabel(
            "Edit Alert Contact" if self.contact else "Add Alert Contact"
        )
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        root.addWidget(title)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(14)

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.name_input.setPlaceholderText("Person name")
        self.phone_input.setPlaceholderText("+919876543210")

        if self.contact:
            self.name_input.setText(self.contact.get("name", ""))
            self.phone_input.setText(self.contact.get("phone_number", ""))

        form.addRow("Name:", self.name_input)
        form.addRow("Phone Number:", self.phone_input)

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

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root.addStretch()
        root.addWidget(buttons)

    # -------------------------------------------------
    def get_data(self):
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()

        # Normalize phone
        phone = re.sub(r"[^0-9+]", "", phone)
        if phone and not phone.startswith("+"):
            phone = "+" + phone

        if not name:
            return None, None, "Name is required."

        if not phone or not re.match(r"^\+\d{8,15}$", phone):
            return None, None, "Invalid phone number format."

        return name, phone, None


# =====================================================
# Alert Phones Tab
# =====================================================
class AlertPhonesTab(QWidget):
    """
    Alert Contacts Management Tab

    Responsibilities:
    - Model-specific alert phone list
    - Add / Edit / Delete contacts
    - Read-only table with action buttons
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_model_id = None
        self.contacts = []

        self._build_ui()
        self._load_models()
        apply_base_dialog_style(self)

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        # ---------------- Header ----------------
        title = QLabel("Alert Contacts")
        title.setObjectName("SectionTitle")
        root.addWidget(title)

        # ---------------- Model selector ----------------
        model_row = QHBoxLayout()
        model_row.setSpacing(12)

        model_label = QLabel("Model:")
        model_label.setMinimumWidth(60)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(320)
        self.model_combo.currentIndexChanged.connect(
            self._on_model_changed
        )

        model_row.addWidget(model_label)
        model_row.addWidget(self.model_combo)
        model_row.addStretch()

        root.addLayout(model_row)

        # ---------------- Add button ----------------
        btn_row = QHBoxLayout()

        self.add_btn = QPushButton("Add Contact")
        self.add_btn.setProperty("role", "primary")
        self.add_btn.clicked.connect(self._add_contact)

        btn_row.addWidget(self.add_btn)
        btn_row.addStretch()

        root.addLayout(btn_row)

        # ---------------- Table ----------------
        self.table = QTableWidget(0, 3)
        self.table.setObjectName("AlertContactsTable")
        self.table.setHorizontalHeaderLabels(
            ["Name", "Phone Number", "Actions"]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)

        self.table.setColumnWidth(2, 260)

        root.addWidget(self.table)

        # ---------------- Status ----------------
        self.status_label = QLabel(
            "Select a model to manage alert contacts"
        )
        self.status_label.setObjectName("MutedText")

        root.addWidget(self.status_label)
        root.addStretch()

    # -------------------------------------------------
    # Data
    # -------------------------------------------------
    def _load_models(self):
        self.model_combo.clear()
        self.model_combo.addItem("— Select a model —", None)

        for model in get_models():
            self.model_combo.addItem(model["name"], model["id"])

    # -------------------------------------------------
    def _on_model_changed(self):
        self.current_model_id = self.model_combo.currentData()

        if not self.current_model_id:
            self.contacts = []
            self.table.setRowCount(0)
            self.status_label.setText(
                "Select a model to manage alert contacts"
            )
            return

        self.status_label.setText("")
        self._load_contacts()

    # -------------------------------------------------
    def _load_contacts(self):
        self.contacts = get_phones_by_model_id(self.current_model_id)
        self.table.setRowCount(len(self.contacts))

        for row, contact in enumerate(self.contacts):
            self.table.setItem(
                row, 0,
                QTableWidgetItem(contact.get("name", ""))
            )
            self.table.setItem(
                row, 1,
                QTableWidgetItem(contact.get("phone_number", ""))
            )

            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(8)

            edit_btn = QPushButton("Edit")
            edit_btn.clicked.connect(
                lambda _, c=contact: self._edit_contact(c)
            )

            delete_btn = QPushButton("Delete")
            delete_btn.setProperty("role", "danger")
            delete_btn.clicked.connect(
                lambda _, cid=contact["id"]: self._delete_contact(cid)
            )

            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()

            self.table.setCellWidget(row, 2, actions)
            self.table.setRowHeight(row, 60)

    # -------------------------------------------------
    # Actions
    # -------------------------------------------------
    def _add_contact(self):
        if not self.current_model_id:
            QMessageBox.warning(
                self,
                "Select Model",
                "Please select a model first."
            )
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
            "Confirm Removal",
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
