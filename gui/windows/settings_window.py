# gui/windows/settings_window.py

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QPushButton, QHBoxLayout, QMessageBox
)
from PySide6.QtCore import Signal, Slot

from backend.models_dao import set_active_model
from gui.windows.models_tab import ModelsTab
from gui.windows.alert_phones_tab import AlertPhonesTab
from gui.windows.change_password_tab import ChangePasswordTab
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """
    System Settings – Central Configuration Dialog

    Responsibilities:
    - Host all settings-related tabs
    - Coordinate model activation lifecycle
    - Emit settings_applied when changes occur

    Styling:
    - Self-contained (via apply_base_dialog_style)
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

        # Apply centralized internal styling
        apply_base_dialog_style(self)

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # ---------------- Tabs ----------------
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, stretch=1)

        self.models_tab = ModelsTab(self)
        self.alert_phones_tab = AlertPhonesTab(self)
        self.password_tab = ChangePasswordTab(self)

        self.tabs.addTab(self.models_tab, "Models")
        self.tabs.addTab(self.alert_phones_tab, "Alert Contacts")
        self.tabs.addTab(self.password_tab, "Change Password")

        # ---------------- Buttons ----------------
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setProperty("role", "secondary")

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setProperty("role", "primary")

        self.btn_close = QPushButton("Close")
        self.btn_close.setProperty("role", "secondary")

        btn_row.addWidget(self.btn_apply)
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_close)

        root.addLayout(btn_row)

    # --------------------------------------------------
    # Signals
    # --------------------------------------------------
    def _connect_signals(self):
        # Dialog buttons
        self.btn_apply.clicked.connect(self.apply)
        self.btn_ok.clicked.connect(self.apply_and_close)
        self.btn_close.clicked.connect(self.reject)

        # Model lifecycle signals
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
            "applied": True
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
