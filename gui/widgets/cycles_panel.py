# gui/widgets/cycles_panel.py

from datetime import datetime
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class CyclesPanel(QFrame):
    """
    Latest Cycles Panel – Production Final (Mode Aware)

    - Fixed height (no scrolling, no interaction)
    - Kiosk-aware sizing
    - Shows recent cycles (newest on top)
    - PASS / FAIL with strong visual priority
    - QR shown only for PASS
    - Deterministic layout (no jumps, no stretch gaps)
    """

    TITLE_HEIGHT = 36
    PANEL_PADDING_V = 14
    PANEL_PADDING_H = 16

    # --------------------------------------------------
    # Init
    # --------------------------------------------------
    def __init__(self, kiosk_mode: bool = False, parent=None):
        super().__init__(parent)

        self.kiosk_mode = kiosk_mode
        self._apply_mode()
        self._build_ui()

    # --------------------------------------------------
    # Mode configuration
    # --------------------------------------------------
    def _apply_mode(self):
        """
        Adjust panel density based on kiosk / windowed mode
        """
        if self.kiosk_mode:
            self.MAX_CYCLES = 9
            self.CARD_HEIGHT = 89
            self.CARD_SPACING = 9
        else:
            self.MAX_CYCLES = 9
            self.CARD_HEIGHT = 86
            self.CARD_SPACING = 9

        self.PANEL_HEIGHT = (
            self.TITLE_HEIGHT
            + (self.MAX_CYCLES * self.CARD_HEIGHT)
            + ((self.MAX_CYCLES - 1) * self.CARD_SPACING)
            + (self.PANEL_PADDING_V * 2)
        )

        self.setFixedHeight(self.PANEL_HEIGHT)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        self.setStyleSheet("""
            QFrame {
                background: #0a0f1a;
                border-radius: 14px;
                border: 1px solid #1a2a3a;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(
            self.PANEL_PADDING_H,
            self.PANEL_PADDING_V,
            self.PANEL_PADDING_H,
            self.PANEL_PADDING_V,
        )
        self.layout.setSpacing(10)

        # -------- Title --------
        title = QLabel("Latest Cycles")
        title.setFixedHeight(self.TITLE_HEIGHT)
        title.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)
        title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        title.setStyleSheet("color: #58a6ff;")
        self.layout.addWidget(title)

        # -------- Cards container --------
        self.card_container = QVBoxLayout()
        self.card_container.setSpacing(self.CARD_SPACING)
        self.card_container.setContentsMargins(0, 0, 0, 0)
        self.layout.addLayout(self.card_container)

    # --------------------------------------------------
    # Update cycles
    # --------------------------------------------------
    def update_cycles(self, cycles: list):
        while self.card_container.count():
            item = self.card_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not cycles:
            empty = QLabel("No cycles recorded")
            empty.setAlignment(Qt.AlignCenter)
            font = QFont("Segoe UI", 13)
            font.setItalic(True)
            empty.setFont(font)
            empty.setStyleSheet("color:#6b7280;")
            empty.setFixedHeight(
                self.MAX_CYCLES * self.CARD_HEIGHT
                + (self.MAX_CYCLES - 1) * self.CARD_SPACING
            )
            self.card_container.addWidget(empty)
            return

        cycles = sorted(
            cycles,
            key=lambda c: datetime.fromisoformat(
                str(c.get("timestamp", "1900-01-01")).replace("Z", "+00:00")
            ),
            reverse=True,
        )

        recent = cycles[:self.MAX_CYCLES]

        for cycle in recent:
            self.card_container.addWidget(self._create_card(cycle))

        # Fill remaining slots to keep height stable
        for _ in range(self.MAX_CYCLES - len(recent)):
            spacer = QFrame()
            spacer.setFixedHeight(self.CARD_HEIGHT)
            self.card_container.addWidget(spacer)

    # --------------------------------------------------
    # Card
    # --------------------------------------------------
    def _create_card(self, cycle: dict) -> QFrame:
        status = (cycle.get("pass_fail") or "").upper()
        is_pass = status == "PASS"

        accent = "#00f5a0" if is_pass else "#ff4d4f"
        fg_main = "#e5e7eb"
        fg_muted = "#9ca3af"

        card = QFrame()
        card.setFixedHeight(self.CARD_HEIGHT)
        
        # CRITICAL FIX: Ensure card background is solid and consistent
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #111827;     /* Use background-color, not just background */
                border-radius: 10px;
                border-left: 6px solid {accent};
                border: 1px solid #1f2937;
            }}
            /* Remove any inherited or default widget backgrounds inside */
            QLabel {{
                background: transparent;
                border: none;
                padding: 0;
                margin: 0;
            }}
        """)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(14)

        # ----- LEFT -----
        left = QVBoxLayout()
        left.setSpacing(4)  # Slightly increased for better readability

        # Model name with depth
        model_name = cycle.get("model_name") or "Unknown"
        depth = cycle.get("peak_height")
        depth_str = f"({depth:.2f} mm)" if depth is not None else "(— mm)"
        model_with_depth = f"{model_name} {depth_str}"

        model_lbl = QLabel(model_with_depth)
        model_lbl.setFont(QFont("Segoe UI", 14, QFont.Bold))
        model_lbl.setStyleSheet(f"color: {accent}; background: transparent;")
        left.addWidget(model_lbl)

        time_lbl = QLabel(self._format_timestamp(cycle.get("timestamp")))
        time_lbl.setFont(QFont("Segoe UI", 12))
        time_lbl.setStyleSheet(f"color: {fg_muted}; background: transparent;")
        left.addWidget(time_lbl)

        layout.addLayout(left, stretch=1)

        # ----- RIGHT -----
        right_label = QLabel()
        right_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        right_label.setFont(QFont("Consolas", 20 if is_pass else 12, QFont.Bold if is_pass else QFont.Normal))
        
        if is_pass:
            qr_value = (
                cycle.get("qr_text")
                or cycle.get("qr_code")
                or cycle.get("qr")
                or "—"
            )
            right_label.setText(qr_value)
            right_label.setStyleSheet("""
                color: #00f5a0;
                background: transparent;
                font-style: normal;
            """)
        else:
            right_label.setText("No QR generated")
            right_label.setStyleSheet("""
                color: #f87171;
                background: transparent;
                font-style: italic;
            """)

        layout.addWidget(right_label, stretch=2)

        return card
    # --------------------------------------------------
    @staticmethod
    def _format_timestamp(ts) -> str:
        if not ts:
            return "—"
        try:
            if isinstance(ts, datetime):
                dt = ts
            else:
                dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y  %H:%M:%S")
        except Exception:
            return "Invalid time"
