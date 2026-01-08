from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox
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
    Models Management – Factory Floor Safe (Final)

    ✔ Independent action buttons
    ✔ No layout nesting inside table cells
    ✔ No hover reliance
    ✔ No clipping issues
    ✔ Predictable sizing
    """

    modelActivated = Signal(int)
    modelSaved = Signal(int)
    modelUpdated = Signal(int)

    ROW_HEIGHT = 56

    # --------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self.models: List[Dict] = []
        self.active_model_id: Optional[int] = None

        self._build_ui()
        self.refresh()

        apply_base_dialog_style(self)

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(16)

        # ---------------- Header ----------------
        header = QHBoxLayout()

        title = QLabel("Quality Control Models")
        title.setObjectName("SectionTitle")

        self.add_btn = QPushButton("Add Model")
        self.add_btn.setProperty("role", "primary")
        self.add_btn.clicked.connect(self._add_model)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.add_btn)

        root.addLayout(header)

        # ---------------- Table ----------------
        self.table = QTableWidget(0, 7)
        self.table.setObjectName("ModelsTable")
        self.table.setHorizontalHeaderLabels([
            "Model Name",
            "Type",
            "Tolerance (mm)",
            "Status",
            "Activate",
            "Edit",
            "Delete"
        ])

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.Stretch)
        header_view.setSectionResizeMode(1, QHeaderView.Fixed)
        header_view.setSectionResizeMode(2, QHeaderView.Stretch)
        header_view.setSectionResizeMode(3, QHeaderView.Fixed)

        for col in (4, 5, 6):
            header_view.setSectionResizeMode(col, QHeaderView.Fixed)
            self.table.setColumnWidth(col, 110)

        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(3, 90)

        root.addWidget(self.table, stretch=1)

    # ==================================================
    # DATA
    # ==================================================
    def refresh(self):
        try:
            self.models = get_models()
        except Exception as exc:
            QMessageBox.critical(self, "Database Error", str(exc))
            self.models = []

        try:
            active = get_active_model()
            self.active_model_id = active["id"] if active else None
        except Exception:
            self.active_model_id = None

        self._render_table()

    # ==================================================
    # TABLE RENDERING
    # ==================================================
    def _render_table(self):
        self.table.setRowCount(len(self.models))

        for row, model in enumerate(self.models):
            self._render_row(row, model)
            self.table.setRowHeight(row, self.ROW_HEIGHT)

    def _render_row(self, row: int, model: Dict):
        is_active = model["id"] == self.active_model_id

        # Model Name
        name_item = QTableWidgetItem(model["name"])
        self._style_item(name_item, is_active)
        self.table.setItem(row, 0, name_item)

        # Type
        type_item = QTableWidgetItem(model.get("model_type", "—"))
        type_item.setTextAlignment(Qt.AlignCenter)
        self._style_item(type_item, is_active)
        self.table.setItem(row, 1, type_item)

        # Tolerance
        tol_item = QTableWidgetItem(
            f"{model['lower_limit']:.2f} – {model['upper_limit']:.2f}"
        )
        self._style_item(tol_item, is_active)
        self.table.setItem(row, 2, tol_item)

        # Status
        status_item = QTableWidgetItem("ACTIVE" if is_active else "INACTIVE")
        status_item.setTextAlignment(Qt.AlignCenter)
        status_item.setForeground(
            QColor("#22c55e") if is_active else QColor("#94a3b8")
        )
        if is_active:
            status_item.setFont(QFont("", weight=QFont.Bold))

        self.table.setItem(row, 3, status_item)

        # ---------- Activate ----------
        btn_activate = QPushButton("Activate")
        btn_activate.setProperty("role", "success")
        btn_activate.setEnabled(not is_active)
        btn_activate.clicked.connect(
            lambda _, m=model: self._activate_model(m)
        )
        self.table.setCellWidget(row, 4, btn_activate)

        # ---------- Edit ----------
        btn_edit = QPushButton("Edit")
        btn_edit.setProperty("role", "secondary")
        btn_edit.clicked.connect(
            lambda _, m=model: self._edit_model(m)
        )
        self.table.setCellWidget(row, 5, btn_edit)

        # ---------- Delete ----------
        btn_delete = QPushButton("Delete")
        btn_delete.setProperty("role", "danger")
        btn_delete.setEnabled(not is_active)
        btn_delete.clicked.connect(
            lambda _, mid=model["id"]: self._delete_model(mid)
        )
        self.table.setCellWidget(row, 6, btn_delete)

    # ==================================================
    # ITEM STYLING
    # ==================================================
    def _style_item(self, item: QTableWidgetItem, is_active: bool):
        if is_active:
            item.setForeground(QColor("#22c55e"))
            item.setFont(QFont("", weight=QFont.Bold))
        else:
            item.setForeground(QColor("#e5e7eb"))

    # ==================================================
    # OPERATIONS
    # ==================================================
    def _add_model(self):
        if ModelEditDialog(self).exec():
            self.refresh()
            if self.models:
                self.modelSaved.emit(self.models[-1]["id"])

    def _edit_model(self, model: Dict):
        if ModelEditDialog(self, model).exec():
            self.refresh()
            self.modelUpdated.emit(model["id"])

    def _delete_model(self, model_id: int):
        if QMessageBox.question(
            self,
            "Confirm Delete",
            "Delete this model?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_model(model_id)
            self.refresh()

    def _activate_model(self, model: Dict):
        if ActivateModelDialog(self, model).exec():
            db_set_active_model(model["id"])
            self.active_model_id = model["id"]
            self.refresh()
            self.modelActivated.emit(model["id"])

    # ==================================================
    # EXTERNAL
    # ==================================================
    def get_active_model_id(self) -> Optional[int]:
        return self.active_model_id

    def persist_active_selection(self):
        if self.active_model_id:
            db_set_active_model(self.active_model_id)
