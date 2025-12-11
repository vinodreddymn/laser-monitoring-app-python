# gui/toast.py  ← FINAL WORKING TOAST
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QPushButton, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QColor


class Toast(QWidget):
    def __init__(self, message, toast_type="info", timeout=5000, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)

        # Icon + Message
        icon_label = QLabel("✓" if toast_type == "success" else "✗" if toast_type == "error" else "ℹ")
        icon_label.setFont(QFont("Segoe UI", 18))
        icon_label.setStyleSheet("color: white;")
        layout.addWidget(icon_label)

        msg_label = QLabel(message)
        msg_label.setFont(QFont("Segoe UI", 11))
        msg_label.setStyleSheet("color: white;")
        layout.addWidget(msg_label)

        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: white;
                border: none;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover { color: #ff6b6b; }
        """)
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

        # Background color
        bg_color = "#27ae60" if toast_type == "success" else "#e74c3c" if toast_type == "error" else "#2c3e50"
        self.setStyleSheet(f"""
            QWidget {{
                background: {bg_color};
                border-radius: 12px;
                min-width: 400px;
            }}
        """)

        # Auto close
        if timeout > 0:
            QTimer.singleShot(timeout, self.close)

        # Slide-in animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(300)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def showEvent(self, event):
        super().showEvent(event)
        self.animation.start()
        # Center top
        if self.parent():
            x = self.parent().width() // 2 - self.width() // 2
            y = 100
            self.move(x, y)