# ======================================================
# gui/windows/history_window.py
# Cycle History Window – Clean & Industrial-Safe
# ======================================================

import logging
from typing import Optional, List, Dict

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton,
    QTableWidget, QTableWidgetItem,
    QDateEdit, QTimeEdit,
    QHeaderView, QMessageBox, QWidget
)
from PySide6.QtCore import Qt, QDateTime, QTime
from PySide6.QtGui import QColor

from backend.cycles_dao import get_cycles_by_datetime
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class HistoryWindow(QDialog):
    """
    Cycle History Window – Read-Only Audit View

    ✔ Preset time ranges
    ✔ PASS / FAIL filtering
    ✔ Date + Time manual selection
    ✔ Summary statistics
    ✔ Highlighted active filters
    ✔ Zero Qt font warnings
    ✔ Industrial-safe implementation
    """

    WIDTH = 1500
    HEIGHT = 900

    # --------------------------------------------------
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self.setWindowTitle("Cycle History")
        self.setModal(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)

        apply_base_dialog_style(self)

        self._result_filter = "ALL"   # ALL | PASS | FAIL
        self._all_cycles: List[Dict] = []
        self._preset_buttons = {}

        self._build_ui()
        self._apply_preset("Last 24h")

    # ==================================================
    # UI BUILD
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(16)

        # ---------------- Header ----------------
        header = QLabel("Cycle History – Audit / Supervisor View")
        header.setAlignment(Qt.AlignLeft)
        root.addWidget(header)

        # ---------------- Preset Row ----------------
        self._build_preset_row(root)

        # ---------------- Filters ----------------
        self._build_filter_row(root)

        # ---------------- Summary ----------------
        self.summary_lbl = QLabel("Total: 0 | PASS: 0 | FAIL: 0")
        self.summary_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.summary_lbl)

        # ---------------- Table ----------------
        self._build_table(root)

        # ---------------- Footer ----------------
        footer = QHBoxLayout()
        footer.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        root.addLayout(footer)

        self._update_result_filter_buttons()

    # ==================================================
    # PRESET ROW
    # ==================================================
    def _build_preset_row(self, root: QVBoxLayout):
        preset_row = QHBoxLayout()
        preset_row.setSpacing(12)

        for label in ("Last 1h", "Today", "Last 24h", "This Week"):
            btn = QPushButton(label)
            btn.setFixedWidth(150)
            btn.clicked.connect(lambda _, l=label: self._apply_preset(l))
            preset_row.addWidget(btn)
            self._preset_buttons[label] = btn

        preset_row.addStretch()
        root.addLayout(preset_row)

    # ==================================================
    # FILTER ROW (Column Based)
    # ==================================================
    def _build_filter_row(self, root: QVBoxLayout):
        filters_row = QHBoxLayout()
        filters_row.setSpacing(24)

        DATE_W = 170
        TIME_W = 170
        BTN_W = 80

        def filter_column(title: str, widget: QWidget, width: int) -> QWidget:
            box = QVBoxLayout()
            box.setSpacing(4)

            lbl = QLabel(title)
            lbl.setAlignment(Qt.AlignLeft)
            widget.setFixedWidth(width)

            box.addWidget(lbl)
            box.addWidget(widget)

            container = QWidget()
            container.setLayout(box)
            return container

        # ---------- Create widgets FIRST ----------

        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)

        self.from_time = QTimeEdit()

        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)

        self.to_time = QTimeEdit()

        # ---------- Now connect signals ----------
        self.from_date.dateChanged.connect(self._clear_preset_highlight)
        self.from_time.timeChanged.connect(self._clear_preset_highlight)
        self.to_date.dateChanged.connect(self._clear_preset_highlight)
        self.to_time.timeChanged.connect(self._clear_preset_highlight)

        # ---------- Add to layout ----------
        filters_row.addWidget(filter_column("From Date", self.from_date, DATE_W))
        filters_row.addWidget(filter_column("From Time", self.from_time, TIME_W))
        filters_row.addWidget(filter_column("To Date", self.to_date, DATE_W))
        filters_row.addWidget(filter_column("To Time", self.to_time, TIME_W))

        # -------- Result Filter --------
        result_box = QVBoxLayout()
        result_box.setSpacing(4)

        result_lbl = QLabel("Result")
        result_box.addWidget(result_lbl)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_all = QPushButton("All")
        self.btn_pass = QPushButton("PASS")
        self.btn_fail = QPushButton("FAIL")

        for btn in (self.btn_all, self.btn_pass, self.btn_fail):
            btn.setFixedWidth(BTN_W)

        self.btn_all.clicked.connect(lambda: self._set_result_filter("ALL"))
        self.btn_pass.clicked.connect(lambda: self._set_result_filter("PASS"))
        self.btn_fail.clicked.connect(lambda: self._set_result_filter("FAIL"))

        btn_row.addWidget(self.btn_all)
        btn_row.addWidget(self.btn_pass)
        btn_row.addWidget(self.btn_fail)

        result_box.addLayout(btn_row)

        result_container = QWidget()
        result_container.setLayout(result_box)
        filters_row.addWidget(result_container)

        filters_row.addStretch()

        # -------- Search Button --------
        search_box = QVBoxLayout()
        search_box.addWidget(QLabel(""))

        search_btn = QPushButton("Search")
        search_btn.setProperty("role", "primary")
        search_btn.setFixedWidth(100)
        search_btn.clicked.connect(self._load_data)

        search_box.addWidget(search_btn)

        search_container = QWidget()
        search_container.setLayout(search_box)
        filters_row.addWidget(search_container)

        root.addLayout(filters_row)

    # ==================================================
    # TABLE
    # ==================================================
    def _build_table(self, root: QVBoxLayout):
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Timestamp",
            "Model",
            "Type",
            "Weld Depth",
            "Result",
            "QR Code",
            "Printed"
        ])

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        root.addWidget(self.table, stretch=1)

    # ==================================================
    # PRESETS & FILTERS
    # ==================================================
    def _apply_preset(self, preset: str):
        now = QDateTime.currentDateTime()

        if preset == "Last 1h":
            start = now.addSecs(-3600)
        elif preset == "Today":
            start = QDateTime(now.date(), QTime(0, 0))
        elif preset == "Last 24h":
            start = now.addDays(-1)
        elif preset == "This Week":
            monday = now.date().addDays(-(now.date().dayOfWeek() - 1))
            start = QDateTime(monday, QTime(0, 0))
        else:
            return

        self.from_date.setDate(start.date())
        self.from_time.setTime(start.time())
        self.to_date.setDate(now.date())
        self.to_time.setTime(now.time())

        self._highlight_preset(preset)
        self._load_data()

    def _highlight_preset(self, preset: str):
        active_style = (
            "background-color:#0078D7;color:white;font-weight:bold;border-radius:4px;"
        )
        for name, btn in self._preset_buttons.items():
            btn.setStyleSheet(active_style if name == preset else "")

    def _set_result_filter(self, value: str):
        self._result_filter = value
        self._update_result_filter_buttons()
        self._populate_table(self._all_cycles)

    def _update_result_filter_buttons(self):
        active_style = (
            "background-color:#0078D7;color:white;font-weight:bold;border-radius:4px;"
        )
        for btn, name in (
            (self.btn_all, "ALL"),
            (self.btn_pass, "PASS"),
            (self.btn_fail, "FAIL"),
        ):
            btn.setStyleSheet(active_style if self._result_filter == name else "")

    # ==================================================
    # DATA LOADING
    # ==================================================
    def _load_data(self):
        from_dt = QDateTime(self.from_date.date(), self.from_time.time())
        to_dt = QDateTime(self.to_date.date(), self.to_time.time())

        if from_dt > to_dt:
            QMessageBox.warning(
                self,
                "Invalid Range",
                "'From' date/time cannot be later than 'To' date/time."
            )
            return

        try:
            self._all_cycles = get_cycles_by_datetime(
                from_dt.toString("yyyy-MM-dd HH:mm:ss"),
                to_dt.toString("yyyy-MM-dd HH:mm:ss"),
            )
        except Exception:
            log.exception("Failed to load cycle history")
            QMessageBox.warning(self, "Error", "Failed to load cycle history.")
            return

        self._populate_table(self._all_cycles)

    # ==================================================
    # TABLE POPULATION
    # ==================================================
    def _populate_table(self, cycles: List[Dict]):
        self.table.setRowCount(0)

        total = pass_cnt = fail_cnt = 0

        for c in cycles:
            result = c.get("pass_fail", "")

            if self._result_filter != "ALL" and result != self._result_filter:
                continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            self._set_item(row, 0, c["timestamp"])
            self._set_item(row, 1, c["model_name"])
            self._set_item(row, 2, c.get("model_type", ""))
            self._set_item(row, 3, f"{c['peak_height']:.2f}")

            result_item = QTableWidgetItem(result)
            result_item.setTextAlignment(Qt.AlignCenter)
            result_item.setForeground(
                QColor("green") if result == "PASS" else QColor("red")
            )
            self.table.setItem(row, 4, result_item)

            self._set_item(row, 5, c.get("qr_code") or "—")

            printed = "YES" if c.get("printed") else "NO"
            printed_item = QTableWidgetItem(printed)
            printed_item.setTextAlignment(Qt.AlignCenter)
            printed_item.setForeground(
                QColor("green") if printed == "YES" else QColor("darkYellow")
            )
            self.table.setItem(row, 6, printed_item)

            total += 1
            pass_cnt += (result == "PASS")
            fail_cnt += (result == "FAIL")

        self.summary_lbl.setText(
            f"Total: {total} | PASS: {pass_cnt} | FAIL: {fail_cnt}"
        )

    # --------------------------------------------------
    def _set_item(self, row: int, col: int, value):
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)

    def _clear_preset_highlight(self):
        """Clear preset button highlight when custom date/time is used."""
        for btn in self._preset_buttons.values():
            btn.setStyleSheet("")

