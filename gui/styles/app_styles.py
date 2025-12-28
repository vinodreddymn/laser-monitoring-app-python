def apply_base_dialog_style(widget):
    widget.setStyleSheet("""
        /* =================================================
           BASE / GLOBAL (SURFACE LAYER)
           ================================================= */
        QWidget {
            background-color: #020617;   /* deep navy */
            color: #e5e7eb;
            font-family: "Segoe UI";
            font-size: 18px;              /* tuned for 1080p */
        }

        /* =================================================
           TITLES & TEXT HIERARCHY
           ================================================= */
        QLabel#DialogTitle {
            font-size: 28px;
            font-weight: 700;
            color: #f9fafb;
        }

        QLabel#SectionTitle {
            font-size: 23px;
            font-weight: 600;
            color: #f1f5f9;
        }

        QLabel#MutedText {
            font-size: 18px;
            color: #9ca3af;
        }

        /* =================================================
           INPUT CONTROLS (RAISED SURFACE)
           ================================================= */
        QLineEdit,
        QComboBox {
            background-color: #020617;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 10px 12px;
            min-height: 36px;
            selection-background-color: #2563eb;
        }

        QLineEdit:hover,
        QComboBox:hover {
            border-color: #64748b;
        }

        QLineEdit:focus,
        QComboBox:focus {
            border-color: #60a5fa;
        }

        /* =================================================
           TABLES (DATA SURFACE)
           ================================================= */
        QTableWidget {
            background-color: #020617;
            border: 1px solid #1e293b;
            alternate-background-color: #020617;
            gridline-color: #1e293b;
        }

        QTableWidget::item {
            padding: 10px;
        }

        QTableWidget::item:selected {
            background-color: #1e293b;
            color: #f8fafc;
        }

        QHeaderView::section {
            background-color: #020617;
            color: #c7d2fe;
            border: none;
            padding: 12px 10px;
            font-weight: 600;
            font-size: 18px;
        }

        /* =================================================
           BUTTONS (ACTION LAYER)
           ================================================= */
        QPushButton {
            background-color: #2563eb;
            color: #ffffff;
            border-radius: 10px;
            padding: 10px 24px;
            font-weight: 600;
            min-height: 38px;
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

        QPushButton[role="secondary"]:hover {
            background-color: #475569;
        }

        QPushButton[role="danger"] {
            background-color: #dc2626;
        }

        QPushButton[role="danger"]:hover {
            background-color: #ef4444;
        }

        QPushButton:disabled {
            background-color: #1e293b;
            color: #64748b;
        }

        /* =================================================
           TABS (NAVIGATION LAYER)
           ================================================= */
        QTabWidget::pane {
            border: 1px solid #1e293b;
            margin-top: -1px;
        }

        QTabBar::tab {
            background-color: #020617;
            padding: 12px 22px;
            border: 1px solid #1e293b;
            border-bottom: none;
            font-size: 18px;
            color: #cbd5f5;
        }

        QTabBar::tab:hover {
            color: #93c5fd;
        }

        QTabBar::tab:selected {
            background-color: #020617;
            color: #60a5fa;
            font-weight: 600;
            border-bottom: 2px solid #60a5fa;
        }
    """)
