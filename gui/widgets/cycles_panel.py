# gui/widgets/cycles_panel.py

from datetime import datetime
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class CyclesPanel(QFrame):
    """
    Redesigned Latest Cycles Panel - Pure Display Only

    - Fixed height, no scrolling, no interaction
    - Shows up to 8 most recent cycles (newest on top)
    - Clear info: Status (PASS/FAIL), Model, Timestamp, QR Text (only on PASS)
    - Compact cards with strong left accent bar
    - Matches dark professional theme
    """

    MAX_CYCLES = 8
    CARD_HEIGHT = 84                   # Reduced height to fit 8 cards comfortably
    PANEL_HEIGHT = 120 + (MAX_CYCLES * CARD_HEIGHT) + (MAX_CYCLES - 1) * 10  # title + cards + spacing

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.PANEL_HEIGHT)
        self._build_ui()

    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #0a0f1a;
                border-radius: 14px;
                border: 1px solid #1a2a3a;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(18, 18, 18, 18)
        self.layout.setSpacing(14)

        # Title
        title = QLabel("Latest Cycles")
        title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        title.setStyleSheet("color: #58a6ff;")
        self.layout.addWidget(title)

        # Container for cycle cards
        self.card_container = QVBoxLayout()
        self.card_container.setSpacing(10)  # Tighter spacing between cards
        self.card_container.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.card_container)

    def update_cycles(self, cycles: list):
        # Clear existing cards
        while self.card_container.count():
            item = self.card_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cycles:
            empty = QLabel("No cycles recorded yet")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #555555; font-size: 15px; font-style: italic;")
            empty.setFixedHeight(self.MAX_CYCLES * self.CARD_HEIGHT + (self.MAX_CYCLES - 1) * 10)
            self.card_container.addWidget(empty)
            return

        # Sort newest first
        cycles = sorted(
            cycles,
            key=lambda c: datetime.fromisoformat(str(c.get("timestamp", "1900-01-01")).replace("Z", "+00:00")),
            reverse=True,
        )

        recent_cycles = cycles[:self.MAX_CYCLES]

        for cycle in recent_cycles:
            self.card_container.addWidget(self._create_card(cycle))

        # Fill remaining slots with invisible spacers to keep fixed height
        displayed = len(recent_cycles)
        for _ in range(self.MAX_CYCLES - displayed):
            spacer = QFrame()
            spacer.setFixedHeight(self.CARD_HEIGHT)
            self.card_container.addWidget(spacer)

    def _create_card(self, cycle: dict) -> QFrame:
        status = (cycle.get("pass_fail") or "").strip().upper()
        is_pass = status == "PASS"

        accent_color = "#00ffaa" if is_pass else "#ff4444"
        text_color = "#ffffff"
        secondary_color = "#aaaaaa"

        card = QFrame()
        card.setFixedHeight(self.CARD_HEIGHT)
        card.setStyleSheet(f"""
            QFrame {{
                background: #11191f;
                border-radius: 9px;
                border-left: 7px solid {accent_color};
                border: 1px solid #222222;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 10, 15, 10)
        layout.setSpacing(16)

        # Left: Status, Model, Timestamp
        left_layout = QVBoxLayout()
        left_layout.setSpacing(3)

        # Status
        status_lbl = QLabel(status or "—")
        status_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        status_lbl.setStyleSheet(f"color: {accent_color};")
        left_layout.addWidget(status_lbl)

        # Model
        model = cycle.get("model_name") or "Unknown Model"
        model_lbl = QLabel(model)
        model_lbl.setFont(QFont("Segoe UI", 12))
        model_lbl.setStyleSheet(f"color: {text_color};")
        left_layout.addWidget(model_lbl)

        # Timestamp
        timestamp = self._format_timestamp(cycle.get("timestamp"))
        time_lbl = QLabel(timestamp)
        time_lbl.setFont(QFont("Segoe UI", 10))
        time_lbl.setStyleSheet(f"color: {secondary_color};")
        left_layout.addWidget(time_lbl)

        layout.addLayout(left_layout, stretch=1)

        # Right: QR Text or failure message
        if is_pass:
            qr_text = cycle.get("qr_text") or cycle.get("qr_code") or "—"
            qr_lbl = QLabel(qr_text)
            qr_lbl.setFont(QFont("Consolas", 17, QFont.Bold))
            qr_lbl.setStyleSheet("color: #00ffaa;")
            qr_lbl.setWordWrap(False)
        else:
            qr_lbl = QLabel("No QR generated")
            qr_lbl.setFont(QFont("Segoe UI", 13))
            qr_lbl.setStyleSheet("color: #f85149; font-style: italic;")

        qr_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(qr_lbl, stretch=2)

        return card

    @staticmethod
    def _format_timestamp(ts) -> str:
        if not ts:
            return "—"
        try:
            if isinstance(ts, datetime):
                dt = ts
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y %H:%M:%S")
        except Exception:
            return "Invalid timestamp"