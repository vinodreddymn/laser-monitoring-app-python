# gui/windows/qr_search_print_tab.py
# ======================================================
# Manual QR Search & Reprint Tab
# ======================================================

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime


from backend.cycles_dao import (
    get_cycle_by_qr_code,
    log_print_event,
)
from backend.live_print import try_print_live_cycle

log = logging.getLogger(__name__)


class QRSearchPrintTab(QWidget):
    """
    Search & Print QR Label (Manual Reprint)

    ✔ Searches cycle by exact QR
    ✔ Shows detailed cycle preview
    ✔ Regenerates QR image if missing
    ✔ Does NOT modify printed flag
    ✔ Logs REPRINT audit
    ✔ Ready for next search after successful print
    """

    # ==================================================
    def __init__(self, parent=None):
        super().__init__(parent)
        self._cycle: Optional[dict] = None
        self._build_ui()

    # ==================================================
    # UI
    # ==================================================
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        # -------- Title --------
        title = QLabel("Search & Print QR Label")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)

        # -------- Search Row --------
        search_row = QHBoxLayout()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter exact QR text here... and press Enter")
        self.search_edit.returnPressed.connect(self._search)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._search)

        search_row.addWidget(QLabel("QR Text"))
        search_row.addWidget(self.search_edit, stretch=1)
        search_row.addWidget(search_btn)

        layout.addLayout(search_row)

        # -------- Preview --------
        self.preview = QLabel("Enter QR text and search.")
        self.preview.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.preview.setMinimumHeight(220)
        self.preview.setTextFormat(Qt.RichText)
        self.preview.setStyleSheet("""
            background: #020617;
            border: 2px dashed #334155;
            border-radius: 12px;
            padding: 24px;
            font-size: 15px;
            font-family: Consolas, Monaco, monospace;
            color: #e5e7eb;
        """)
        layout.addWidget(self.preview, stretch=1)

        # -------- Action Buttons --------
        action_row = QHBoxLayout()

        self.clear_btn = QPushButton("Clear / New Search")
        self.clear_btn.setEnabled(False)
        self.clear_btn.clicked.connect(self._reset_for_next_search)

        self.print_btn = QPushButton("Print QR Label")
        self.print_btn.setProperty("role", "primary")
        self.print_btn.setEnabled(False)
        self.print_btn.clicked.connect(self._print)

        action_row.addWidget(self.clear_btn)
        action_row.addStretch()
        action_row.addWidget(self.print_btn)

        layout.addLayout(action_row)


    # ==================================================
    # SEARCH
    # ==================================================
    def _search(self):
        qr_text = self.search_edit.text().strip()

        if not qr_text:
            QMessageBox.warning(self, "Invalid Input", "Please enter QR text.")
            return

        try:
            cycle = get_cycle_by_qr_code(qr_text)
        except Exception:
            log.exception("QR search failed")
            QMessageBox.critical(
                self,
                "Search Error",
                "Failed to search QR.\nPlease check system logs.",
            )
            return

        if not cycle:
            self._clear_preview()
            QMessageBox.information(self, "Not Found", "QR not found.")
            return

        # -------- Validate mandatory fields --------
        if not cycle.get("cycle_id"):
            log.error("Invalid cycle record returned: %s", cycle)
            QMessageBox.critical(
                self,
                "Data Error",
                "Invalid cycle data returned.\nContact administrator.",
            )
            return

        self._cycle = cycle

        # -------- Derived / formatted fields --------
        peak = cycle.get("peak_height")
        model_type = cycle.get("model_type", "N/A")
        peak_text = f"{peak:.2f} mm" if isinstance(peak, (int, float)) else "—"

        raw_ts = cycle.get("timestamp")

        if isinstance(raw_ts, datetime):
            timestamp = raw_ts.strftime("%d-%m-%Y %H:%M:%S")
        elif isinstance(raw_ts, str):
            try:
                timestamp = datetime.strptime(
                    raw_ts, "%Y-%m-%d %H:%M:%S"
                ).strftime("%d-%m-%Y %H:%M:%S")
            except ValueError:
                timestamp = raw_ts  # fallback (already formatted or unexpected)
        else:
            timestamp = "—"


        printed_flag = bool(cycle.get("printed", False))
        printed_text = "YES" if printed_flag else "NO"
        printed_color = "#f59e0b" if printed_flag else "#22c55e"

        result = cycle.get("pass_fail", "—")
        result_color = (
            "#22c55e" if result == "PASS"
            else "#ef4444" if result == "FAIL"
            else "#94a3b8"
        )

        # -------- Preview (Rich HTML) --------
        self.preview.setText(f"""
        <div style="
            font-size:28px;
            font-weight:800;
            margin-bottom:20px;
            text-align:left;
        ">
            QR :
            <span style="color:#38bdf8; font-size:34px;">
                {cycle['qr_code']}
            </span>
        </div>

        <table style="
            width:100%;
            border-collapse:collapse;
            font-size:20px;
        ">
            <tr>
                <td style="padding:8px 0; color:#94a3b8; width:40%;">
                    Model
                </td>
                <td style="padding:8px 0; font-weight:600;">
                    {cycle.get("model_name", "—")}
                </td>
            </tr>

             <tr>
                <td style="padding:8px 0; color:#94a3b8; width:40%;">
                    Model Type
                </td>
                <td style="padding:8px 0; font-weight:600;">
                    {cycle.get("model_type", "—")}
                </td>
            </tr>
                       <tr>
                <td style="padding:8px 0; color:#94a3b8;">
                    Result
                </td>
                <td style="
                    padding:8px 0;
                    font-weight:800;
                    color:{result_color};
                    font-size:22px;
                ">
                    {result}
                </td>
            </tr>

            <tr>
                <td style="padding:8px 0; color:#94a3b8;">
                    Weld Depth (Peak)
                </td>
                <td style="padding:8px 0;">
                    {peak_text}
                </td>
            </tr>

            <tr>
                <td style="padding:8px 0; color:#94a3b8;">
                    Cycle Timestamp
                </td>
                <td style="padding:8px 0;">
                    {timestamp}
                </td>
            </tr>

            <tr>
                <td style="padding:8px 0; color:#94a3b8;">
                    Printed Earlier
                </td>
                <td style="
                    padding:8px 0;
                    font-weight:800;
                    color:{printed_color};
                    font-size:22px;
                ">
                    {printed_text}
                </td>
            </tr>
        </table>
        """)


        self.print_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)


        log.info(
            "QR search successful",
            extra={
                "qr_code": cycle["qr_code"],
                "cycle_id": cycle["cycle_id"],
            },
        )

    # ==================================================
    # PRINT
    # ==================================================
    def _print(self):
        if not self._cycle:
            return

        cycle = self._cycle

        cycle_row = {
            # Unified ID (printer + audit)
            "id": cycle["cycle_id"],
            "cycle_id": cycle["cycle_id"],

            # QR identity
            "qr_code": cycle["qr_code"],
            "qr_code_id": cycle["qr_code"],

            # Image (may be None → regen)
            "qr_image_path": cycle.get("qr_image_path"),

            # Required for regen
            "model_name": cycle.get("model_name", "UNKNOWN"),
            "model_type": cycle.get("model_type") or "RHD",
            "peak_height": cycle.get("peak_height", 0.0),
            "timestamp": cycle.get("timestamp"),

            "pass_fail": cycle.get("pass_fail"),
        }

        ok, err = try_print_live_cycle(cycle_row)

        if not ok:
            QMessageBox.critical(
                self,
                "Print Failed",
                err or "QR printing failed.",
            )
            return

        # -------- Audit (REPRINT) --------
        # -------- Audit (REPRINT) --------
        try:
            log_print_event(
                cycle_id=cycle["cycle_id"],
                print_type="REPRINT",
                printed_by="OPERATOR",
                reason="Manual QR search reprint",
            )
        except Exception:
            log.exception("Failed to log reprint audit")

        QMessageBox.information(
            self,
            "Print Successful",
            f"QR label printed successfully.\n\nQR: {cycle['qr_code']}",
        )

        # ✅ Reset UI for next QR (do NOT close window)
        self._reset_for_next_search()


    # ==================================================
    # HELPERS
    # ==================================================
    def _clear_preview(self):
        self._cycle = None
        self.preview.setText("Enter QR text and search.")
        self.print_btn.setEnabled(False)

    def _reset_for_next_search(self):
        self._cycle = None
        self.search_edit.clear()
        self.preview.setText("Enter QR text and search.")
        self.print_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        self.search_edit.setFocus()


        # Cursor back to QR input for operator
        self.search_edit.setFocus()

    def _close_parent_dialog(self):
        """
        Close parent dialog if embedded inside QDialog / tab dialog.
        """
        parent = self.parent()
        while parent:
            if hasattr(parent, "accept"):
                parent.accept()
                return
            parent = parent.parent()
