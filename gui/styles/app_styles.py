def apply_base_dialog_style(widget):
    widget.setStyleSheet("""
        /* =================================================
           BASE / GLOBAL
           ================================================= */
        QWidget {
            background-color: #020617;
            color: #e5e7eb;
            font-family: "Segoe UI";
            font-size: 13px;                 /* ↑ from 12px */
        }

        /* =================================================
           TITLES & TEXT
           ================================================= */
        QLabel#DialogTitle {
            font-size: 20px;                /* ↑ clearer hierarchy */
            font-weight: 700;
            color: #f8fafc;
        }

        QLabel#SectionTitle {
            font-size: 17px;
            font-weight: 600;
            color: #f1f5f9;
        }

        QLabel#MutedText {
            font-size: 13px;
            color: #94a3b8;
        }

        /* =================================================
           INPUTS
           ================================================= */
        QLineEdit,
        QComboBox {
            background-color: #020617;
            border: 1px solid #334155;
            border-radius: 8px;             /* ↑ softer */
            padding: 8px 10px;              /* ↑ better touch target */
            min-height: 34px;
        }

        QLineEdit:focus,
        QComboBox:focus {
            border-color: #3b82f6;
        }

        /* =================================================
           TABLES
           ================================================= */
        QTableWidget {
            background-color: #020617;
            border: 1px solid #1e293b;
            alternate-background-color: #020617;
            gridline-color: #1e293b;
        }

        QHeaderView::section {
            background-color: #020617;
            color: #cbd5f5;
            border: none;
            padding: 10px 8px;              /* ↑ readability */
            font-weight: 600;
            font-size: 13px;
        }

        QTableWidget::item {
            padding: 6px;
        }

        QTableWidget::item:selected {
            background-color: #1e293b;
        }

        /* =================================================
           BUTTONS
           ================================================= */
        QPushButton {
            background-color: #2563eb;
            color: #ffffff;
            border-radius: 10px;
            padding: 8px 20px;              /* ↑ hit area */
            font-weight: 600;
            min-height: 36px;
        }

        QPushButton:hover {
            background-color: #3b82f6;
        }

        QPushButton:pressed {
            background-color: #1d4ed8;
        }

        QPushButton[role="secondary"] {
            background-color: #334155;
        }

        QPushButton[role="danger"] {
            background-color: #dc2626;
        }

        QPushButton:disabled {
            background-color: #1e293b;
            color: #64748b;
        }

        /* =================================================
           TABS
           ================================================= */
        QTabWidget::pane {
            border: 1px solid #1e293b;
        }

        QTabBar::tab {
            background: #020617;
            padding: 10px 20px;             /* ↑ better spacing */
            border: 1px solid #1e293b;
            border-bottom: none;
            font-size: 13px;
        }

        QTabBar::tab:selected {
            background: #020617;
            color: #60a5fa;
            font-weight: 600;
        }

        QTabBar::tab:hover {
            color: #93c5fd;
        }
    """)
