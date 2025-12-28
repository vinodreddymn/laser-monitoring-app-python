from typing import Optional

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Signal, Slot

from backend.models_dao import set_active_model
from gui.windows.models_tab import ModelsTab
from gui.windows.alert_phones_tab import AlertPhonesTab

log = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """
    System Settings – Central Configuration Dialog

    Responsibilities:
    - Host settings tabs
    - React to model activation
    - Emit settings_applied when changes occur

    Styling:
    - styles/dialogs.qss
    """

    settings_applied = Signal(dict)

    WIDTH = 920
    HEIGHT = 660

    # --------------------------------------------------
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SettingsWindow")
        self.setWindowTitle("System Settings")
        self.setModal(True)
        self.setMinimumSize(self.WIDTH, self.HEIGHT)

        self._build_ui()
        self._connect_signals()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ---------------- Tabs ----------------
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, stretch=1)

        self.models_tab = ModelsTab(self)
        self.tabs.addTab(self.models_tab, "Models")

        self.alert_phones_tab = AlertPhonesTab(self)
        self.tabs.addTab(self.alert_phones_tab, "Alert Contacts")

        # ---------------- Buttons ----------------
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_apply = QPushButton("Apply")
        self.btn_ok = QPushButton("OK")
        self.btn_close = QPushButton("Close")

        btn_row.addWidget(self.btn_apply)
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_close)

        layout.addLayout(btn_row)

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------
    def _connect_signals(self):
        # Buttons
        self.btn_apply.clicked.connect(self.apply)
        self.btn_ok.clicked.connect(self.apply_and_close)
        self.btn_close.clicked.connect(self.reject)

        # Model lifecycle
        self.models_tab.modelActivated.connect(self._on_model_changed)
        self.models_tab.modelSaved.connect(self._on_model_changed)
        self.models_tab.modelUpdated.connect(self._on_model_changed)

    # --------------------------------------------------
    # Model handling
    # --------------------------------------------------
    @Slot(int)
    def _on_model_changed(self, model_id: int):
        """
        Centralized model activation point
        """
        try:
            set_active_model(model_id)
            log.info("Active model set → %s", model_id)
        except Exception:
            log.exception("Failed to set active model")

        self.settings_applied.emit({
            "model_id": model_id,
            "applied": True,
        })

    # --------------------------------------------------
    # Apply logic
    # --------------------------------------------------
    @Slot()
    def apply(self):
        """
        Apply settings without closing dialog
        """
        try:
            # Persist model selection if tab supports it
            if hasattr(self.models_tab, "persist_active_selection"):
                self.models_tab.persist_active_selection()
        except Exception:
            log.exception("Failed to persist model selection")

        self.settings_applied.emit({"applied": True})

        QMessageBox.information(
            self,
            "Settings Applied",
            "Settings have been applied successfully."
        )

    @Slot()
    def apply_and_close(self):
        self.apply()
        self.accept()
