import re
import logging
from typing import List, Dict, Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QMessageBox,
    QLineEdit,
    QFormLayout,
    QDialog,
    QDialogButtonBox,
    QFrame,
     QSizePolicy
)
from PySide6.QtCore import Qt

from backend.models_dao import get_models
from backend.alert_phones_dao import (
    get_phones_by_model_id,
    add_phone,
    update_phone,
    delete_phone
)
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)

MAX_NAME_LENGTH = 45
PHONE_DIGITS = 10
COUNTRY_CODE = "+91"


# =====================================================
# Alert Contact Add / Edit Dialog
# =====================================================
class PhoneEditDialog(QDialog):
    """
    Alert Contact Dialog – Factory Safe

    • Add / Edit alert contacts
    • Strong phone validation
    • Fixed-size, distraction-free
    """

    WIDTH = 500
    HEIGHT = 300

    # --------------------------------------------------
    def __init__(self, parent=None, contact: Optional[Dict] = None):
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

    # --------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        # ---------------- Title ----------------
        title = QLabel(self.windowTitle())
        title.setObjectName("DialogTitle")
        title.setAlignment(Qt.AlignCenter)
        root.addWidget(title)

        # ---------------- Form ----------------
        form = QFormLayout()
        form.setSpacing(16)

        self.name_input = QLineEdit()
        self.phone_input = QLineEdit()

        self.name_input.setPlaceholderText("Person name")
        self.phone_input.setPlaceholderText("+919876543210")
        self.name_input.setMaxLength(MAX_NAME_LENGTH)
        self.phone_input.setMaxLength(PHONE_DIGITS)
        self.phone_input.setPlaceholderText("10 digit mobile number")

        if self.contact:
            self.name_input.setText(self.contact.get("name", ""))

            # Show only last 10 digits in edit mode
            phone = self.contact.get("phone_number", "")
            phone_digits = re.sub(r"\D", "", phone)

            if phone_digits.endswith(phone_digits[-PHONE_DIGITS:]):
                phone_digits = phone_digits[-PHONE_DIGITS:]

            self.phone_input.setText(phone_digits)

        form.addRow("Name", self.name_input)
        form.addRow("Phone Number", self.phone_input)

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

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        root.addWidget(buttons)

    # --------------------------------------------------
    def get_data(self):
        """
        Validate and normalize input
        """
        name = self.name_input.text().strip()
        phone = self.phone_input.text().strip()

        # ---------------- Name Validation ----------------
        if not name:
            return None, None, "Name is required."

        if len(name) > MAX_NAME_LENGTH:
            return (
                None,
                None,
                f"Name must be less than {MAX_NAME_LENGTH} characters."
            )

        # ---------------- Phone Validation ----------------
        # Remove anything except digits
        phone_digits = re.sub(r"\D", "", phone)

        if len(phone_digits) != PHONE_DIGITS:
            return (
                None,
                None,
                "Phone number must contain exactly 10 digits."
            )

        # Always store in +91 format
        phone_final = f"{COUNTRY_CODE}{phone_digits}"

        return name, phone_final, None



# =====================================================
# Alert Phones Tab
# =====================================================
class AlertPhonesTab(QWidget):
    """
    Alert Contacts – Model Specific

    Responsibilities
    ----------------
    • Select model
    • Manage alert phone list
    • Add / Edit / Delete contacts
    """

    ROW_HEIGHT = 72

    # --------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_model_id: Optional[int] = None
        self.contacts: List[Dict] = []

        self._build_ui()
        self._load_models()

        apply_base_dialog_style(self)

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 28, 28, 28)
        root.setSpacing(20)

        # ---------------- Header ----------------
        header = QLabel("Alert Contacts")
        header.setObjectName("SectionTitle")
        root.addWidget(header)

        # ---------------- Model Selector ----------------
        selector = QFrame()
        selector_layout = QHBoxLayout(selector)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(12)

        model_label = QLabel("Model")
        model_label.setMinimumWidth(60)

        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(360)
        self.model_combo.currentIndexChanged.connect(
            self._on_model_changed
        )

        selector_layout.addWidget(model_label)
        selector_layout.addWidget(self.model_combo)
        selector_layout.addStretch()

        root.addWidget(selector)

        # ---------------- Add Button ----------------
        action_row = QHBoxLayout()
        self.add_btn = QPushButton("Add Contact")
        self.add_btn.setProperty("role", "primary")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self._add_contact)

        action_row.addWidget(self.add_btn)
        action_row.addStretch()

        root.addLayout(action_row)

        # ---------------- Table ----------------
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

        self.table.setColumnWidth(2, 280)

        # ✅ CRITICAL FIXES
        self.table.setMinimumHeight(420)   # show many rows
        self.table.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )

        root.addWidget(self.table)

        # ---------------- Status ----------------
        self.status_label = QLabel("Select a model to manage alert contacts")
        self.status_label.setObjectName("MutedText")
        root.addWidget(self.status_label)

    # ==================================================
    # DATA
    # ==================================================
    def _load_models(self):
        self.model_combo.clear()
        self.model_combo.addItem("— Select a model —", None)

        for model in get_models():
            self.model_combo.addItem(model["name"], model["id"])

    # --------------------------------------------------
    def _on_model_changed(self):
        self.current_model_id = self.model_combo.currentData()
        self.add_btn.setEnabled(bool(self.current_model_id))

        if not self.current_model_id:
            self.contacts = []
            self.table.setRowCount(0)
            self.status_label.setText(
                "Select a model to manage alert contacts"
            )
            return

        self.status_label.setText("")
        self._load_contacts()

    # --------------------------------------------------
    def _load_contacts(self):
        self.contacts = get_phones_by_model_id(self.current_model_id)
        self.table.setRowCount(len(self.contacts))

        for row, contact in enumerate(self.contacts):
            self._render_row(row, contact)

    # --------------------------------------------------
    def _render_row(self, row: int, contact: Dict):
        self.table.setItem(
            row, 0, QTableWidgetItem(contact.get("name", ""))
        )
        self.table.setItem(
            row, 1, QTableWidgetItem(contact.get("phone_number", ""))
        )

        actions = QWidget()
        layout = QHBoxLayout(actions)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        edit_btn = QPushButton("Edit")
        edit_btn.setProperty("role", "secondary")
        edit_btn.clicked.connect(
            lambda _, c=contact: self._edit_contact(c)
        )

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("role", "danger")
        delete_btn.clicked.connect(
            lambda _, cid=contact["id"]: self._delete_contact(cid)
        )

        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        layout.addStretch()

        self.table.setCellWidget(row, 2, actions)
        self.table.setRowHeight(row, self.ROW_HEIGHT)

    # ==================================================
    # ACTIONS
    # ==================================================
    def _add_contact(self):
        dlg = PhoneEditDialog(self)
        if dlg.exec() != QDialog.Accepted:
            return

        name, phone, error = dlg.get_data()
        if error:
            QMessageBox.warning(self, "Invalid Data", error)
            return

        add_phone(self.current_model_id, name, phone)
        self._load_contacts()

    # --------------------------------------------------
    def _edit_contact(self, contact: Dict):
        dlg = PhoneEditDialog(self, contact)
        if dlg.exec() != QDialog.Accepted:
            return

        name, phone, error = dlg.get_data()
        if error:
            QMessageBox.warning(self, "Invalid Data", error)
            return

        update_phone(contact["id"], name, phone)
        self._load_contacts()

    # --------------------------------------------------
    def _delete_contact(self, contact_id: int):
        reply = QMessageBox.question(
            self,
            "Confirm Removal",
            "Remove this alert contact?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            delete_phone(contact_id)
            self._load_contacts()

    # ==================================================
    # API FOR SETTINGS WINDOW
    # ==================================================
    def get_all_phone_records(self):
        return list(self.contacts)
