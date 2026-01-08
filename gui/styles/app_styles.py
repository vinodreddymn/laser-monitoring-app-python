def apply_base_dialog_style(widget):
    """
    Simplified industrial dark theme for factory floor use.

    Goals:
    - High readability
    - Stable layout (no hover jitter)
    - Clear table structure
    - Minimal styling rules
    - Easy long-term maintenance
    """
    widget.setStyleSheet("""
    /* =================================================
       GLOBAL BASE
       ================================================= */
    QWidget, QDialog {
        background-color: #020617;
        color: #e5e7eb;
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: 16px;
    }

    QFrame {
        background: transparent;
    }

    /* =================================================
       TEXT HIERARCHY
       ================================================= */
    QLabel#DialogTitle {
        font-size: 24px;
        font-weight: 700;
        color: #f8fafc;
        padding: 6px 0;
    }

    QLabel#SectionTitle {
        font-size: 20px;
        font-weight: 600;
        color: #e2e8f0;
        padding: 6px 0;
    }

    QLabel#MutedText {
        font-size: 15px;
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
        min-height: 38px;
    }

    QLineEdit:focus,
    QComboBox:focus,
    QSpinBox:focus,
    QDoubleSpinBox:focus {
        border-color: #60a5fa;
    }

    QLineEdit:disabled,
    QComboBox:disabled {
        color: #64748b;
        border-color: #1e293b;
    }

    /* Dropdown list */
    QComboBox QAbstractItemView {
        background-color: #020617;
        color: #e5e7eb;
        border: 1px solid #334155;
        selection-background-color: #1e293b;
        selection-color: #f8fafc;
    }

    /* =================================================
       BUTTONS (NO HOVER EFFECTS)
       ================================================= */
    QPushButton {
        background-color: #1e293b;
        color: #f8fafc;
        border: none;
        border-radius: 6px;
        padding: 8px 18px;
        min-height: 38px;
        font-weight: 600;
    }

    QPushButton:pressed {
        background-color: #0f172a;
    }

    QPushButton[role="primary"] {
        background-color: #2563eb;
    }

    QPushButton[role="success"] {
        background-color: #16a34a;
    }

    QPushButton[role="danger"] {
        background-color: #dc2626;
    }

    QPushButton:disabled {
        background-color: #1e293b;
        color: #64748b;
    }

    /* Compact buttons inside tables */
    QTableWidget QPushButton {
        padding: 4px 10px;
        min-height: 30px;
        font-size: 14px;
    }

    /* =================================================
       TABLES – CLEAR BORDERS
       ================================================= */
    QTableWidget {
        background-color: #020617;
        border: 2px solid #334155;     /* outer border */
        gridline-color: #334155;
        font-size: 16px;
    }

    QTableWidget::item {
        padding: 10px;
        border-bottom: 1px solid #334155;
        border-right: 1px solid #1e293b;
    }

    QTableWidget::item:selected {
        background-color: #1e293b;
        color: #f8fafc;
    }

    QHeaderView::section {
        background-color: #020617;
        color: #cbd5f5;
        padding: 10px;
        font-weight: 600;
        border-right: 1px solid #334155;
        border-bottom: 2px solid #334155;
    }

    QHeaderView::section:last {
        border-right: none;
    }

    /* =================================================
       TABS
       ================================================= */
    QTabWidget::pane {
        border: 1px solid #334155;
    }

    QTabBar::tab {
        background-color: #020617;
        color: #94a3b8;
        padding: 10px 24px;
        font-size: 16px;
    }

    QTabBar::tab:selected {
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
       MESSAGE BOXES
       ================================================= */
    QMessageBox {
        background-color: #020617;
        color: #e5e7eb;
    }

    QMessageBox QPushButton {
        min-width: 90px;
    }
    """)
