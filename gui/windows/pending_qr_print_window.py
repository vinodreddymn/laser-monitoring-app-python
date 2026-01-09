import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QLabel,
    QHeaderView, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

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
    Industrial-grade Pending QR Print Window

    Features:
    - Checkbox-based multi selection
    - Auto refresh
    - Center-aligned content
    - PASS / FAIL semantic coloring
    - Safe manual print workflow
    """

    WIDTH = 1300
    HEIGHT = 900
    AUTO_REFRESH_MS = 10_000  # 10 seconds

    # ==================================================
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Pending QR Label Printing")
        self.setModal(True)
        self.setMinimumSize(self.WIDTH, self.HEIGHT)

        base_font = self.font()
        base_font.setPointSize(11)
        self.setFont(base_font)

        self.cycles = []

        self._build_ui()
        apply_base_dialog_style(self)

        self._setup_auto_refresh()
        self.refresh()

    # ==================================================
    # UI BUILD
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(24, 24, 24, 20)

        root.addWidget(self._build_header())
        root.addWidget(self._build_status())

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Sl. No",
            "✓",
            "QR Code",
            "Timestamp",
            "Model",
            "Type",
            "Depth",
            "Result",
        ])

        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)

        table_font = QFont()
        table_font.setPointSize(11)
        self.table.setFont(table_font)

        self.table.setStyleSheet(self._table_stylesheet())

        header = self.table.horizontalHeader()
        header.setHighlightSections(False)
        header.setSectionResizeMode(QHeaderView.Fixed)

        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 180)
        self.table.setColumnWidth(3, 210)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 120)
        self.table.setColumnWidth(6, 120)
        header.setSectionResizeMode(7, QHeaderView.Stretch)

        self.table.itemChanged.connect(self._on_item_changed)
        self.table.cellClicked.connect(self._on_cell_clicked)

        root.addWidget(self.table, stretch=1)
        root.addWidget(self._build_footer())

        # Empty table overlay message
        self.empty_lbl = QLabel("NO PENDING QR LABELS TO PRINT", self.table)
        self.empty_lbl.setAlignment(Qt.AlignCenter)

        self.empty_lbl.setStyleSheet("""
            QLabel {
                color: #64748b;          /* Muted industrial grey */
                background: transparent;
                font-size: 30px;         /* FORCE size (this works) */
                font-weight: 700;
            }
        """)

        self.empty_lbl.hide()

    
    
    # --------------------------------------------------
    def _build_header(self):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 10)

        title = QLabel("Pending QR Labels")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)

        subtitle = QLabel("Manual Print Queue")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle.setFont(subtitle_font)

        layout.addWidget(title)
        layout.addSpacing(16)
        layout.addWidget(subtitle)
        layout.addStretch()

        return frame

    # --------------------------------------------------
    def _build_status(self):
        self.status_lbl = QLabel("")
        self.status_lbl.setAlignment(Qt.AlignCenter)

        status_font = QFont()
        status_font.setPointSize(12)
        status_font.setBold(True)
        self.status_lbl.setFont(status_font)
        self.status_lbl.setMinimumHeight(32)

        return self.status_lbl

    # --------------------------------------------------
    def _build_footer(self):
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 15, 0, 0)
        layout.setSpacing(16)

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.setMinimumHeight(36)
        self.select_all_btn.clicked.connect(self._toggle_select_all)

        self.print_btn = QPushButton("Print Selected")
        self.print_btn.setProperty("role", "primary")
        self.print_btn.setMinimumWidth(180)
        self.print_btn.setMinimumHeight(36)
        self.print_btn.clicked.connect(self._print_selected)

        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.clicked.connect(self.accept)

        layout.addWidget(self.select_all_btn)
        layout.addStretch()
        layout.addWidget(self.print_btn)
        layout.addWidget(close_btn)

        return frame

    # ==================================================
    # STYLES
    # ==================================================
    @staticmethod
    def _table_stylesheet():
        return """
        QTableWidget {
            background-color: #0f172a;
            gridline-color: #334155;
            border: 1px solid #475569;
            border-radius: 8px;
            color: #e5e7eb;
            selection-background-color: #1e40af;
            selection-color: #ffffff;
        }

        QTableWidget::item {
            padding: 8px 10px;
            border-bottom: 1px solid #1e293b;
            color: #e5e7eb;
        }

        QTableWidget::item:alternate {
            background-color: #020617;
        }

        QTableWidget::item:hover {
            background-color: #1e293b;
        }

        QHeaderView::section {
            background-color: #020617;
            color: #f8fafc;
            border: 1px solid #334155;
            padding: 10px 8px;
            font-weight: 600;
            text-align: center;
        }

        QTableWidget::indicator {
            width: 18px;
            height: 18px;
        }

        QTableWidget::indicator:checked {
            background-color: #22c55e;
            border: 1px solid #16a34a;
        }

        QTableWidget::indicator:unchecked {
            background-color: #020617;
            border: 1px solid #475569;
        }
        """

    # ==================================================
    # AUTO REFRESH
    # ==================================================
    def _setup_auto_refresh(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(self.AUTO_REFRESH_MS)

    # ==================================================
    # DATA HANDLING
    # ==================================================
    def refresh(self):
        try:
            new_cycles = get_pending_qr_cycles()
        except Exception:
            log.exception("Failed to fetch pending QR cycles")
            self.status_lbl.setText("⚠ Failed to load pending QR labels")
            return

        selected_qrs = self._get_selected_qrs()

        self.cycles = new_cycles
        self._populate_table()
        self._restore_selection(selected_qrs)
        self._update_status()

        # ---- EMPTY TABLE MESSAGE ----
        if not self.cycles:
            QTimer.singleShot(0, self._show_empty_message)
        else:
            self.empty_lbl.hide()


    def _show_empty_message(self):
        self.empty_lbl.setGeometry(self.table.viewport().rect())
        self.empty_lbl.raise_()
        self.empty_lbl.show()

    # --------------------------------------------------
    def _populate_table(self):
        self.table.clearContents()
        self.table.setRowCount(len(self.cycles))

        for row, cycle in enumerate(self.cycles):
            self._add_row(row, cycle)

    # --------------------------------------------------
    def _center_item(self, text):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        return item

    # --------------------------------------------------
    def _add_row(self, r, cycle):
        self.table.setItem(r, 0, self._center_item(r + 1))

        chk = QTableWidgetItem()
        chk.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable)
        chk.setCheckState(Qt.Unchecked)
        chk.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(r, 1, chk)

        self.table.setItem(r, 2, self._center_item(cycle["qr_code"]))
        self.table.setItem(r, 3, self._center_item(cycle["timestamp"]))
        self.table.setItem(r, 4, self._center_item(cycle["model_name"]))
        self.table.setItem(r, 5, self._center_item(cycle.get("model_type", "")))
        self.table.setItem(r, 6, self._center_item(cycle["peak_height"]))

        result_item = self._center_item(cycle["pass_fail"])
        if cycle["pass_fail"] == "PASS":
            result_item.setForeground(Qt.green)
        elif cycle["pass_fail"] == "FAIL":
            result_item.setForeground(Qt.red)

        self.table.setItem(r, 7, result_item)

    # ==================================================
    # SELECTION
    # ==================================================
    def _get_selected_qrs(self):
        selected = set()
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and item.checkState() == Qt.Checked:
                selected.add(self.table.item(r, 2).text())
        return selected

    def _restore_selection(self, selected_qrs):
        for r in range(self.table.rowCount()):
            if self.table.item(r, 2).text() in selected_qrs:
                self.table.item(r, 1).setCheckState(Qt.Checked)

    def _toggle_select_all(self):
        all_checked = all(
            self.table.item(r, 1).checkState() == Qt.Checked
            for r in range(self.table.rowCount())
        )

        for r in range(self.table.rowCount()):
            self.table.item(r, 1).setCheckState(
                Qt.Unchecked if all_checked else Qt.Checked
            )

        self._update_status()

    # --------------------------------------------------
    def _on_item_changed(self, item):
        if item.column() == 1:
            self._update_status()

    def _on_cell_clicked(self, row, column):
        if column != 1:
            chk = self.table.item(row, 1)
            if chk:
                chk.setCheckState(
                    Qt.Unchecked if chk.checkState() == Qt.Checked else Qt.Checked
                )

    # --------------------------------------------------
    def _update_status(self):
        self.status_lbl.setText(
            f"Total Pending: {len(self.cycles)} | "
            f"Selected for Print: {len(self._get_selected_qrs())}"
        )

    # ==================================================
    # PRINTING
    # ==================================================
    def _print_selected(self):
        selected_cycles = [
            c for c in self.cycles
            if c["qr_code"] in self._get_selected_qrs()
        ]

        if not selected_cycles:
            QMessageBox.information(self, "No Selection", "No QR labels selected.")
            return

        if QMessageBox.question(
            self,
            "Confirm Print",
            f"Print {len(selected_cycles)} selected QR labels?",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        self.print_btn.setEnabled(False)

        printed, failed = 0, []

        for cycle in selected_cycles:
            ok, err = try_print_live_cycle({
                "id": cycle["id"],
                "qr_code": cycle["qr_code"],
                "qr_code_id": cycle["qr_code"],
                "qr_image_path": cycle["qr_image_path"],
                "model_name": cycle["model_name"],
                "pass_fail": cycle["pass_fail"],
            })

            if ok:
                mark_printed(cycle["id"])
                log_print_event(
                    cycle_id=cycle["id"],
                    print_type="MANUAL",
                    printed_by="OPERATOR",
                    reason=None,
                )
                printed += 1
            else:
                failed.append(f"{cycle['qr_code']} – {err}")

        self.print_btn.setEnabled(True)
        self.refresh()

        if failed:
            QMessageBox.warning(
                self,
                "Print Completed with Errors",
                f"Printed: {printed}\n\nFailed:\n" + "\n".join(failed),
            )
        else:
            QMessageBox.information(
                self,
                "Print Successful",
                f"Successfully printed {printed} QR labels.",
            )
