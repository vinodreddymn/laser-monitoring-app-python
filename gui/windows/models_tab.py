# gui/windows/models_tab.py

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from backend.models_dao import (
    get_models,
    add_model,
    update_model,
    delete_model,
    set_active_model as db_set_active_model
)

from .model_edit_dialog import ModelEditDialog
from .activate_model_dialog import ActivateModelDialog


class ModelsTab(QWidget):
    # ✅ SIGNALS REQUIRED BY SettingsWindow
    modelActivated = Signal(int)
    modelSaved = Signal(int)
    modelUpdated = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.models = []
        self.active_model_id = None

        self.setup_ui()
        self.refresh()

    # ---------------------------------------------------
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Header
        header = QHBoxLayout()
        header.addWidget(QLabel("<h2 style='color:#1e293b; margin:0;'>Quality Control Models</h2>"))
        header.addStretch()

        add_btn = QPushButton("+ Add New Model")
        add_btn.setStyleSheet("background:#3b82f6; color:white; padding:10px 20px; border-radius:8px; font-weight:600;")
        add_btn.clicked.connect(self.add_new_model)
        header.addWidget(add_btn)

        layout.addLayout(header)

        # Table
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Model", "Type", "Tolerance (mm)", "Status", "Actions"]
        )

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)


        layout.addWidget(self.table)

    # ---------------------------------------------------
    def refresh(self):
        self.models = get_models()
        self.table.setRowCount(len(self.models))

        # get current active model from DB (if you store it there)
        try:
            from backend.models_dao import get_active_model
            active = get_active_model()
            self.active_model_id = active["id"] if active else None
        except Exception:
            self.active_model_id = None

        for i, model in enumerate(self.models):
            mid = model["id"]

            # ------------------------------------------------
            # Model Name
            # ------------------------------------------------
            self.table.setItem(i, 0, QTableWidgetItem(model["name"]))

            # ------------------------------------------------
            # Model Type (RHD / LHD)
            # ------------------------------------------------
            model_type = model.get("model_type") or "—"
            type_item = QTableWidgetItem(model_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setForeground(Qt.GlobalColor.darkBlue)
            self.table.setItem(i, 1, type_item)

            # ------------------------------------------------
            # Limits
            # ------------------------------------------------
            self.table.setItem(
                i, 2,
                QTableWidgetItem(f"{model['lower_limit']:.2f} – {model['upper_limit']:.2f}")
            )

            # ------------------------------------------------
            # Status
            # ------------------------------------------------
            status = "Active" if mid == self.active_model_id else "Inactive"
            status_item = QTableWidgetItem(status)

            if status == "Active":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.gray)

            self.table.setItem(i, 3, status_item)

            # ------------------------------------------------
            # Actions
            # ------------------------------------------------
            actions = QWidget()
            hlay = QHBoxLayout(actions)
            hlay.setContentsMargins(5, 5, 5, 5)

            activate = QPushButton("Activate")
            activate.setStyleSheet("background:#10b981; color:white; padding:6px 12px; border-radius:6px;")
            activate.clicked.connect(lambda _, m=model: self.activate_model(m))

            edit = QPushButton("Edit")
            edit.setStyleSheet("background:#3b82f6; color:white; padding:6px 12px; border-radius:6px;")
            edit.clicked.connect(lambda _, m=model: self.edit_model(m))

            delete = QPushButton("Delete")
            delete.setStyleSheet("background:#ef4444; color:white; padding:6px 12px; border-radius:6px;")
            delete.clicked.connect(lambda _, mid=mid: self.delete_model(mid))

            for btn in (activate, edit, delete):
                hlay.addWidget(btn)

            self.table.setCellWidget(i, 4, actions)

    # ---------------------------------------------------
    def add_new_model(self):
        dialog = ModelEditDialog(self)
        if dialog.exec():
            self.refresh()
            # ✅ emit last added as "saved"
            if self.models:
                self.modelSaved.emit(self.models[-1]["id"])

    # ---------------------------------------------------
    def edit_model(self, model):
        dialog = ModelEditDialog(self, model)
        if dialog.exec():
            self.refresh()
            self.modelUpdated.emit(model["id"])

    # ---------------------------------------------------
    def delete_model(self, model_id):
        reply = QMessageBox.question(self, "Confirm", "Delete this model and all its alert phones?")
        if reply == QMessageBox.StandardButton.Yes:
            delete_model(model_id)
            self.refresh()

    # ---------------------------------------------------
    # ✅ CRITICAL FIX: ACTIVATE MODEL
    # ---------------------------------------------------
    def activate_model(self, model):
        dialog = ActivateModelDialog(self, model)

        if dialog.exec():
            try:
                model_id = model["id"]

                # ✅ PERSIST ACTIVE MODEL
                db_set_active_model(model_id)

                # ✅ UPDATE LOCAL STATE
                self.active_model_id = model_id
                self.refresh()

                # ✅ EMIT SIGNAL TO SettingsWindow → MainWindow → Live Page
                self.modelActivated.emit(model_id)

            except Exception as e:
                QMessageBox.critical(self, "Activation Failed", str(e))

    # ---------------------------------------------------
    # ✅ USED BY SettingsWindow
    # ---------------------------------------------------
    def get_active_model_id(self):
        return self.active_model_id

    # ---------------------------------------------------
    def persist_active_selection(self):
        if self.active_model_id:
            try:
                db_set_active_model(self.active_model_id)
            except Exception:
                pass
