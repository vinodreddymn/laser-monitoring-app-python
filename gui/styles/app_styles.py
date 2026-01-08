def apply_base_dialog_style(widget):
    """
    Simple, professional industrial dark theme.

    Design goals:
    - Calm, low-fatigue visuals
    - High readability on factory floor
    - Stable layout (no hover jitter)
    - Easy long-term maintenance
    """
    widget.setStyleSheet("""
    /* =================================================
       GLOBAL BASE
       ================================================= */
    QWidget {
        background-color: #020617;
        color: #e5e7eb;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 18px;
    }

    QDialog {
        border: 2px solid #334155;
    }

    QFrame {
        background: transparent;
    }

    /* =================================================
       HEADERS
       ================================================= */
    QFrame#HeaderFrame {
        background-color: #0b1220;
        border-bottom: 2px solid #334155;
        padding: 14px 20px;
    }

    QLabel#DialogTitle {
        font-size: 22px;
        font-weight: 600;
        color: #f8fafc;
    }

    QLabel#SectionTitle {
        font-size: 18px;
        font-weight: 600;
        color: #e2e8f0;
        margin-top: 10px;
    }

    QLabel#MutedText {
        font-size: 14px;
        color: #94a3b8;
    }

    /* =================================================
       INPUT CONTROLS
       ================================================= */
    QLineEdit,
    QComboBox,
    QSpinBox,
    QDoubleSpinBox {
        background-color: #020617;
        color: #e5e7eb;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 8px 12px;
        min-height: 36px;
    }

    QLineEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus {
        border-color: #60a5fa;
        outline: none;
    }

    QLineEdit:disabled,
    QComboBox:disabled {
        color: #64748b;
        border-color: #1e293b;
    }

    QComboBox QAbstractItemView {
        background-color: #020617;
        border: 1px solid #334155;
        selection-background-color: #1e293b;
    }

    /* =================================================
   BUTTONS
   ================================================= */
    QPushButton {
        background-color: #0f172a;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 6px;
        padding: 8px 18px;
        min-height: 36px;
        font-weight: 600;
    }

    QPushButton:hover {
        background-color: #1e293b;
    }

    QPushButton:pressed {
        background-color: #020617;
    }

    QPushButton[role="primary"] {
        background-color: #1d4ed8;
        border-color: #3b82f6;
    }

    QPushButton[role="success"] {
        background-color: #15803d;
        border-color: #22c55e;
    }

    QPushButton[role="danger"] {
        background-color: #b91c1c;
        border-color: #ef4444;
    }

    /* ===== TABLE ACTION BUTTONS ===== */
    QTableWidget QPushButton {
        min-width: 90px;
        min-height: 28px;
        padding: 4px 12px;
        font-size: 14px;
        font-weight: 600;
    }


    /* =================================================
       TABLES
       ================================================= */
    QTableWidget {
        background-color: #020617;
        border: 2px solid #334155;
        gridline-color: #334155;
        font-size: 17px;
    }

    QTableWidget::item {
        padding: 10px;
        border-bottom: 1px solid #334155;
    }

    QTableWidget::item:selected {
        background-color: #1e293b;
        color: #f8fafc;
    }

    QHeaderView::section {
        background-color: #0b1220;
        color: #cbd5f5;
        padding: 10px;
        font-weight: 600;
        border-bottom: 2px solid #334155;
        border-right: 1px solid #334155;
    }

    QHeaderView::section:last {
        border-right: none;
    }

    /* =================================================
       TABS
       ================================================= */
    QTabWidget::pane {
        border: 2px solid #334155;
        background-color: #020617;
    }

    QTabBar::tab {
        background-color: #020617;
        color: #94a3b8;
        padding: 10px 24px;
        font-size: 17px;
        border: 1px solid #334155;
        border-bottom: none;
        margin-right: 2px;
    }

    QTabBar::tab:selected {
        background-color: #0f172a;
        color: #60a5fa;
        border-bottom: 3px solid #60a5fa;
        font-weight: 600;
    }

    /* =================================================
       SCROLLBARS
       ================================================= */
    QScrollBar:vertical {
        background: #020617;
        width: 10px;
    }

    QScrollBar::handle:vertical {
        background: #334155;
        border-radius: 5px;
    }

    QScrollBar::add-line,
    QScrollBar::sub-line {
        height: 0;
    }

    /* =================================================
   MESSAGE BOXES – ROLE AWARE (SHUTDOWN SAFE)
   ================================================= */
    QMessageBox {
        background-color: #020617;
        color: #e5e7eb;
        border: 2px solid #334155;
        font-size: 18px;
    }

    /* Message text */
    QMessageBox QLabel#qt_msgbox_label {
        min-width: 420px;
        line-height: 1.4;
        padding: 8px 0;
    }

    /* Icon spacing */
    QMessageBox QLabel#qt_msgboxex_icon_label {
        padding-right: 12px;
    }

    /* -------------------------------------------------
    Buttons – Base
    ------------------------------------------------- */
    QMessageBox QPushButton {
        min-width: 120px;
        min-height: 38px;
        padding: 6px 20px;
        font-weight: 600;
        border-radius: 6px;
    }

    /* -------------------------------------------------
    Primary (Cancel / Safe Action)
    ------------------------------------------------- */
    QMessageBox QPushButton[role="primary"] {
        background-color: #1d4ed8;
        border: 1px solid #3b82f6;
        color: #f8fafc;
    }

    QMessageBox QPushButton[role="primary"]:hover {
        background-color: #2563eb;
    }

    /* -------------------------------------------------
    Danger (Shutdown / Destructive)
    ------------------------------------------------- */
    QMessageBox QPushButton[role="danger"] {
        background-color: #b91c1c;
        border: 1px solid #ef4444;
        color: #fef2f2;
    }

    QMessageBox QPushButton[role="danger"]:hover {
        background-color: #dc2626;
    }

    /* -------------------------------------------------
    Default fallback
    ------------------------------------------------- */
    QMessageBox QPushButton:!enabled {
        background-color: #0f172a;
        color: #64748b;
        border-color: #374151;
    }


    """)
