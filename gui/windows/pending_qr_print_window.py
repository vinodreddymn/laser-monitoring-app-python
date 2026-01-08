# ======================================================
# Pending QR Print Window (Self-Styled, Modal)
# ======================================================

import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLabel, QHeaderView
)
from PySide6.QtCore import Qt

from backend.cycles_dao import (
    get_pending_qr_cycles,
    mark_printed,
    log_print_event,
)
from backend.live_print import try_print_live_cycle

from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class PendingQRPrintWindow(QDialog):
    """
    Modal window to manually print pending QR codes.
    Uses shared styling for uniformity.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pending QR Labels")
        self.setModal(True)
        self.setMinimumSize(1000, 500)

        self._build_ui()
        apply_base_dialog_style(self)
        self.refresh()

    # --------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(14, 14, 14, 14)

        # ---------- Title ----------
        title = QLabel("Pending QR Labels – Manual Print")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignLeft)
        root.addWidget(title)

        # ---------- Info ----------
        self.info_lbl = QLabel("")
        self.info_lbl.setObjectName("Info")
        self.info_lbl.setAlignment(Qt.AlignCenter)
        root.addWidget(self.info_lbl)

        # ---------- Table ----------
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "QR Code",
            "Timestamp",
            "Model",
            "Peak",
            "Result",
            "Action",
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        root.addWidget(self.table, stretch=1)

        # ---------- Buttons ----------
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        btn_row.addWidget(refresh_btn)

        close_btn = QPushButton("Close")
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    # --------------------------------------------------
    def refresh(self):
        self.table.setRowCount(0)
        self.info_lbl.setText("")

        try:
            rows = get_pending_qr_cycles()
        except Exception:
            log.exception("Failed to fetch pending QR cycles")
            self.info_lbl.setText("⚠ Failed to load pending QR labels.")
            return

        if not rows:
            self.info_lbl.setText("No pending QR labels to print.")
            return

        for row in rows:
            self._add_row(row)

    # --------------------------------------------------
    def _add_row(self, cycle: dict):
        r = self.table.rowCount()
        self.table.insertRow(r)

        self.table.setItem(r, 0, QTableWidgetItem(cycle["qr_code"]))

        self.table.setItem(r, 1, QTableWidgetItem(str(cycle["timestamp"])))
        self.table.setItem(r, 2, QTableWidgetItem(cycle["model_name"]))
        self.table.setItem(r, 3, QTableWidgetItem(str(cycle["peak_height"])))
        self.table.setItem(r, 4, QTableWidgetItem(cycle["pass_fail"]))

        btn = QPushButton("Print")
        btn.setObjectName("printBtn")
        btn.clicked.connect(lambda _, c=cycle: self._print_cycle(c))
        self.table.setCellWidget(r, 5, btn)

    # --------------------------------------------------
    def _print_cycle(self, cycle: dict):
        ok, err = try_print_live_cycle(
            {
                "id": cycle["id"],
                "qr_code": cycle["qr_code"],
                "qr_code_id": cycle["qr_code"],
                "qr_image_path": cycle["qr_image_path"],
                "model_name": cycle["model_name"],
                "pass_fail": cycle["pass_fail"],
            }
        )

        if not ok:
            QMessageBox.warning(
                self,
                "Print Failed",
                f"Failed to print QR label:\n{err}",
            )
            return

        try:
            mark_printed(cycle["id"])

            log_print_event(
                cycle_id=cycle["id"],
                print_type="MANUAL",
                printed_by="OPERATOR",
                reason=None,
            )

            QMessageBox.information(
                self,
                "Print Successful",
                f"QR label printed for Cycle ID {cycle['id']}",
            )

            self.refresh()

        except Exception as e:
            QMessageBox.warning(
                self,
                "Database Error",
                f"Printed but failed to update database:\n{e}",
            )
