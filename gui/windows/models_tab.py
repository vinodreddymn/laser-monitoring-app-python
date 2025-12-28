# gui/windows/models_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from backend.models_dao import (
    get_models,
    delete_model,
    set_active_model as db_set_active_model,
    get_active_model
)

from gui.styles.app_styles import apply_base_dialog_style
from .model_edit_dialog import ModelEditDialog
from .activate_model_dialog import ActivateModelDialog


class ModelsTab(QWidget):
    """
    Models Management Tab

    Responsibilities:
    - List QC models
    - Add / edit / delete models
    - Activate exactly ONE model
    - Notify SettingsWindow when model changes
    """

    # Signals consumed by SettingsWindow
    modelActivated = Signal(int)
    modelSaved = Signal(int)
    modelUpdated = Signal(int)

    # -------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self.models = []
        self.active_model_id = None

        self._build_ui()
        self.refresh()

        apply_base_dialog_style(self)

    # -------------------------------------------------
    # UI
    # -------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(22)
        root.setContentsMargins(28, 28, 28, 28)

        # ---------------- HEADER ----------------
        header = QHBoxLayout()
        header.setSpacing(12)

        title = QLabel("Quality Control Models")
        title.setObjectName("SectionTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))

        add_btn = QPushButton("Add New Model")
        add_btn.setMinimumHeight(36)
        add_btn.setProperty("role", "primary")
        add_btn.clicked.connect(self.add_new_model)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(add_btn)

        root.addLayout(header)

        # ---------------- TABLE ----------------
        self.table = QTableWidget(0, 5)
        self.table.setObjectName("ModelsTable")
        self.table.setHorizontalHeaderLabels(
            ["Model", "Type", "Tolerance (mm)", "Status", "Actions"]
        )

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)   # Model
        header.setSectionResizeMode(1, QHeaderView.Fixed)     # Type
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Tolerance
        header.setSectionResizeMode(3, QHeaderView.Fixed)    # Status
        header.setSectionResizeMode(4, QHeaderView.Fixed)    # Actions

        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 320)

        root.addWidget(self.table)

    # -------------------------------------------------
    # DATA
    # -------------------------------------------------
    def refresh(self):
        self.models = get_models()

        try:
            active = get_active_model()
            self.active_model_id = active["id"] if active else None
        except Exception:
            self.active_model_id = None

        self.table.setRowCount(len(self.models))

        for row, model in enumerate(self.models):
            self._populate_row(row, model)

    # -------------------------------------------------
    def _populate_row(self, row: int, model: dict):
        model_id = model["id"]
        is_active = model_id == self.active_model_id

        # ---------------- MODEL NAME ----------------
        name_item = QTableWidgetItem(model["name"])
        self._apply_active_style(name_item, is_active)
        self.table.setItem(row, 0, name_item)

        # ---------------- TYPE ----------------
        type_item = QTableWidgetItem(model.get("model_type", "—"))
        type_item.setTextAlignment(Qt.AlignCenter)
        self._apply_active_style(type_item, is_active)
        self.table.setItem(row, 1, type_item)

        # ---------------- TOLERANCE ----------------
        tol_text = (
            f"{model['lower_limit']:.2f} – {model['upper_limit']:.2f}"
        )
        tol_item = QTableWidgetItem(tol_text)
        self._apply_active_style(tol_item, is_active)
        self.table.setItem(row, 2, tol_item)

        # ---------------- STATUS ----------------
        status_item = QTableWidgetItem(
            "ACTIVE" if is_active else "INACTIVE"
        )
        status_item.setTextAlignment(Qt.AlignCenter)

        if is_active:
            status_item.setForeground(QColor("#22c55e"))
            status_item.setFont(QFont("Segoe UI", weight=QFont.Bold))
        else:
            status_item.setForeground(QColor("#94a3b8"))

        self.table.setItem(row, 3, status_item)

        # ---------------- ACTIONS ----------------
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        activate_btn = QPushButton("Activate")
        activate_btn.setEnabled(not is_active)
        activate_btn.clicked.connect(
            lambda _, m=model: self.activate_model(m)
        )

        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(
            lambda _, m=model: self.edit_model(m)
        )

        delete_btn = QPushButton("Delete")
        delete_btn.setProperty("role", "danger")
        delete_btn.clicked.connect(
            lambda _, mid=model_id: self.delete_model(mid)
        )

        actions_layout.addWidget(activate_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        actions_layout.addStretch()

        self.table.setCellWidget(row, 4, actions_widget)
        self.table.setRowHeight(row, 64)

    # -------------------------------------------------
    def _apply_active_style(self, item: QTableWidgetItem, is_active: bool):
        """
        Apply consistent visual style for active vs inactive rows
        """
        if is_active:
            item.setForeground(QColor("#22c55e"))
            item.setFont(QFont("Segoe UI", weight=QFont.Bold))
        else:
            item.setForeground(QColor("#cbd5f5"))

    # -------------------------------------------------
    # ACTIONS
    # -------------------------------------------------
    def add_new_model(self):
        dlg = ModelEditDialog(self)
        if dlg.exec():
            self.refresh()
            if self.models:
                self.modelSaved.emit(self.models[-1]["id"])

    def edit_model(self, model: dict):
        dlg = ModelEditDialog(self, model)
        if dlg.exec():
            self.refresh()
            self.modelUpdated.emit(model["id"])

    def delete_model(self, model_id: int):
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this model and all associated alert contacts?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            delete_model(model_id)
            self.refresh()

    def activate_model(self, model: dict):
        dlg = ActivateModelDialog(self, model)

        if dlg.exec():
            model_id = model["id"]
            try:
                db_set_active_model(model_id)
                self.active_model_id = model_id
                self.refresh()
                self.modelActivated.emit(model_id)
            except Exception as exc:
                QMessageBox.critical(
                    self, "Activation Failed", str(exc)
                )

    # -------------------------------------------------
    # Used by SettingsWindow
    # -------------------------------------------------
    def get_active_model_id(self):
        return self.active_model_id

    def persist_active_selection(self):
        if self.active_model_id:
            try:
                db_set_active_model(self.active_model_id)
            except Exception:
                pass
