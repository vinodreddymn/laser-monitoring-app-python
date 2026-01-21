# ======================================================
# gui/windows/history_window.py
# Cycle History Window – Simplified & Warning-Free
# ======================================================

import logging
from typing import Optional

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

    ✔ Date + Time range filtering (no QDateTimeEdit)
    ✔ PASS / FAIL summary
    ✔ QR Code & Printed status
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

        self._build_ui()
        self._load_data()  # load last 24h by default

    # ==================================================
    # UI BUILD
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(14)

        # ---------------- Header ----------------
        header = QLabel("Cycle History – Audit / Supervisor View")
        header.setAlignment(Qt.AlignLeft)
        root.addWidget(header)

        # ---------------- Filters ----------------
        filter_row = QHBoxLayout()
        filter_row.setSpacing(10)

        filter_row.addWidget(QLabel("From Date:"))
        self.from_date = QDateEdit(QDateTime.currentDateTime().date().addDays(-1))
        self.from_date.setCalendarPopup(True)
        filter_row.addWidget(self.from_date)

        filter_row.addWidget(QLabel("From Time:"))
        self.from_time = QTimeEdit(QTime(0, 0, 0))
        filter_row.addWidget(self.from_time)

        filter_row.addSpacing(20)

        filter_row.addWidget(QLabel("To Date:"))
        self.to_date = QDateEdit(QDateTime.currentDateTime().date())
        self.to_date.setCalendarPopup(True)
        filter_row.addWidget(self.to_date)

        filter_row.addWidget(QLabel("To Time:"))
        self.to_time = QTimeEdit(QDateTime.currentDateTime().time())
        filter_row.addWidget(self.to_time)

        filter_row.addStretch()

        search_btn = QPushButton("Search")
        search_btn.setProperty("role", "primary")
        search_btn.clicked.connect(self._load_data)
        filter_row.addWidget(search_btn)

        root.addLayout(filter_row)

        # ---------------- Summary ----------------
        self.summary_lbl = QLabel("Total: 0 | PASS: 0 | FAIL: 0")
        self.summary_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.summary_lbl)

        # ---------------- Table ----------------
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Timestamp",
            "Model",
            "Type",
            "Peak Height",
            "Result",
            "QR Code",
            "Printed"
        ])

        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)

        root.addWidget(self.table, stretch=1)

        # ---------------- Footer ----------------
        footer = QHBoxLayout()
        footer.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)

        root.addLayout(footer)

    # ==================================================
    # DATA LOADING
    # ==================================================
    def _load_data(self):
        from_dt = QDateTime(self.from_date.date(), self.from_time.time())
        to_dt = QDateTime(self.to_date.date(), self.to_time.time())

        from_ts = from_dt.toString("yyyy-MM-dd HH:mm:ss")
        to_ts = to_dt.toString("yyyy-MM-dd HH:mm:ss")

        try:
            cycles = get_cycles_by_datetime(from_ts, to_ts)
        except Exception:
            log.exception("Failed to load cycle history")
            QMessageBox.warning(self, "Error", "Failed to load cycle history.")
            return

        self.table.setRowCount(len(cycles))

        total = pass_cnt = fail_cnt = 0

        for r, c in enumerate(cycles):
            self._set_item(r, 0, c["timestamp"])
            self._set_item(r, 1, c["model_name"])
            self._set_item(r, 2, c.get("model_type", ""))
            self._set_item(r, 3, f"{c['peak_height']:.2f}")

            # Result
            result = c.get("pass_fail", "")
            result_item = QTableWidgetItem(result)
            result_item.setTextAlignment(Qt.AlignCenter)

            if result == "PASS":
                result_item.setForeground(QColor("green"))
                pass_cnt += 1
            elif result == "FAIL":
                result_item.setForeground(QColor("red"))
                fail_cnt += 1

            self.table.setItem(r, 4, result_item)

            # QR Code
            self._set_item(r, 5, c.get("qr_code") or "—")

            # Printed
            printed = "YES" if c.get("printed") else "NO"
            printed_item = QTableWidgetItem(printed)
            printed_item.setTextAlignment(Qt.AlignCenter)
            printed_item.setForeground(
                QColor("green") if printed == "YES" else QColor("darkYellow")
            )
            self.table.setItem(r, 6, printed_item)

            total += 1

        self.summary_lbl.setText(
            f"Total: {total} | PASS: {pass_cnt} | FAIL: {fail_cnt}"
        )

    # --------------------------------------------------
    def _set_item(self, row: int, col: int, value):
        item = QTableWidgetItem(str(value))
        item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, col, item)
