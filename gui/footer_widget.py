# gui/footer_widget.py

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel


class FooterWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_label = None
        self._build()

    def _build(self):
        fbox = QHBoxLayout(self)
        fbox.setContentsMargins(20, 8, 20, 8)

        self.status_label = QLabel("PLC: OFFLINE")
        fbox.addWidget(self.status_label)
        fbox.addStretch()

    def update_plc_status(self, status: str):
        color = "#10b981" if status == "ONLINE" else "#ef4444"
        self.status_label.setText(f"PLC: {status}")
        self.status_label.setStyleSheet(f"color:{color}; font-weight:bold;")