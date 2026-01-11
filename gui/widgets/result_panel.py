# gui/widgets/result_panel.py

from datetime import datetime
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtGui import QFont, QFontMetrics
from PySide6.QtCore import Qt, QTimer


class ResultPanel(QFrame):
    """
    Enhanced Result Panel with adaptive font sizing and smart wrapping
    for variable-length model names and QR texts (including underscore-separated).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            ResultPanel {
                background: #0a0a0a;
                border-radius: 14px;
                border: 1px solid #222;
            }
        """)

        root = QHBoxLayout(self)
        root.setContentsMargins(32, 32, 32, 32)
        root.setSpacing(40)

        # LEFT: Status + Details
        left_layout = QVBoxLayout()
        left_layout.setSpacing(24)
        left_layout.setAlignment(Qt.AlignCenter)

        self.status_lbl = QLabel("Waiting for cycle...")
        self.status_lbl.setFont(QFont("Segoe UI", 48, QFont.Bold))
        self.status_lbl.setAlignment(Qt.AlignCenter)
        self.status_lbl.setStyleSheet("color: #888;")

        self.details_lbl = QLabel("")
        self.details_lbl.setFont(QFont("Segoe UI", 24))
        self.details_lbl.setAlignment(Qt.AlignCenter)
        self.details_lbl.setWordWrap(True)
        self.details_lbl.setStyleSheet("color: #ccc;")
        self.details_lbl.setOpenExternalLinks(False)

        left_layout.addWidget(self.status_lbl)
        left_layout.addWidget(self.details_lbl)

        # RIGHT: QR Text (large monospace, adaptive)
        self.qr_lbl = QLabel("—")
        self.qr_lbl.setAlignment(Qt.AlignCenter)
        self.qr_lbl.setFont(QFont("Consolas", 55, QFont.Bold))
        self.qr_lbl.setWordWrap(True)
        self.qr_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.qr_lbl.setStyleSheet("""
            background: #111;
            border: 2px solid #333;
            border-radius: 12px;
            color: #666;
            padding: 40px;
        """)

        root.addLayout(left_layout, stretch=4)
        root.addWidget(self.qr_lbl, stretch=6)

    def _allow_wrap_at_underscores(self, text: str) -> str:
        """
        Insert zero-width spaces after underscores to enable line breaking
        at those points without changing visual appearance.
        """
        if not text:
            return text
        return text.replace("_", "_\u200B")  # \u200B = zero-width space

    def _adjust_font_to_fit(self, label: QLabel, text: str, base_size: int, min_size: int = 14):
        """
        Reduce font size dynamically until the text fits comfortably
        within the label's available width.
        """
        if not text or label.width() <= 0:
            return

        # Temporarily set the text to measure accurately
        label.setText(text)

        available_width = label.width() - 80  # Approximate padding/margins

        font = QFont(label.font())
        font.setPointSize(base_size)
        label.setFont(font)

        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(text)

        current_size = base_size
        while text_width > available_width and current_size > min_size:
            current_size -= 2
            font.setPointSize(current_size)
            label.setFont(font)
            metrics = QFontMetrics(font)
            text_width = metrics.horizontalAdvance(text)

    def update_result(self, cycle: dict):
        status = cycle.get("pass_fail", "UNKNOWN")
        weld_depth = float(cycle.get("weld_depth", 0.0))
        model_type = cycle.get("model_type", "N/A")
        model = cycle.get("model_name", "Unknown")
        qr_text = cycle.get("qr_text", "").strip() or "—"

        ts = cycle.get("timestamp", datetime.now())
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))

        time_str = ts.strftime("%d %b %Y, %H:%M:%S")

        # === Status and styling ===
        if status == "PASS":
            self.status_lbl.setText("PASS")
            self.status_lbl.setStyleSheet("""
                color: #00ffaa;
            """)
            border_color = "#00ffaa"
            glow = "0 0 30px #00ffaa44"
            qr_color = "#00ffaa"
        elif status == "FAIL":
            self.status_lbl.setText("FAIL")
            self.status_lbl.setStyleSheet("color: #ff4444;")
            border_color = "#ff4444"
            glow = "0 0 24px #ff444455"
            qr_color = "#666"
            qr_text = "—"
        else:
            self.status_lbl.setText("Waiting for cycle...")
            self.status_lbl.setStyleSheet("color: #888;")
            border_color = "#333"
            glow = "none"
            qr_color = "#666"

        # Apply style to QR box
        self.qr_lbl.setStyleSheet(f"""
            background: #111;
            border: 2px solid {border_color};
            border-radius: 12px;
            color: {qr_color};
            padding: 40px;
        """)

        # === Details text ===
        details_text = (
            f"<b>Model:</b> {model} ({model_type})<br>"
            f"<b>Weld Depth:</b> {weld_depth:.2f} mm<br>"
            f"<b>Time:</b> {time_str}"
        )
        self.details_lbl.setText(details_text)

        # === QR text with smart wrapping ===
        display_qr_text = self._allow_wrap_at_underscores(qr_text)
        self.qr_lbl.setText(display_qr_text)

        # === Adaptive font sizing (after layout update) ===
        QTimer.singleShot(0, lambda: self._adjust_font_to_fit(
            self.qr_lbl, display_qr_text, base_size=80, min_size=32))

        QTimer.singleShot(0, lambda: self._adjust_font_to_fit(
            self.details_lbl, details_text, base_size=30, min_size=18))

    def show_error(self, text: str):
        self.status_lbl.setText(text)
        self.status_lbl.setStyleSheet("color: #ff4444;")

        self.qr_lbl.setStyleSheet("""
            background: #111;
            border: 2px solid #ff4444;
            border-radius: 12px;
            color: #666;
            padding: 40px;
        """)

        self.details_lbl.setText("")
        self.qr_lbl.setText("—")