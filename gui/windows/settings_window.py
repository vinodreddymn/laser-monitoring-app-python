import logging
from typing import Dict

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QPushButton,
    QMessageBox,
    QFrame
)
from PySide6.QtCore import Signal, Slot, Qt

from backend.models_dao import set_active_model
from gui.windows.models_tab import ModelsTab
from gui.windows.alert_phones_tab import AlertPhonesTab
from gui.windows.change_password_tab import ChangePasswordTab
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class SettingsWindow(QDialog):
    """
    System Settings – Factory Floor Configuration Panel

    Purpose
    -------
    • Central configuration for system supervisors
    • Model management, alert contacts, security
    • Safe apply / commit workflow

    Design Principles
    -----------------
    • Stable layout (no visual jump)
    • Clear action separation
    • Touch & mouse friendly
    • 1920x1080 optimized
    """

    settings_applied = Signal(dict)

    WIDTH = 1280
    HEIGHT = 1000

    # ==================================================
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("SettingsWindow")
        self.setWindowTitle("System Settings")
        self.setModal(True)
        self.setMinimumSize(self.WIDTH, self.HEIGHT)

        self._build_ui()
        self._connect_signals()

        apply_base_dialog_style(self)

    # ==================================================
    # UI CONSTRUCTION
    # ==================================================
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 20)
        root.setSpacing(18)

        # ---------------- HEADER ----------------
        header = self._build_header()
        root.addWidget(header)

        # ---------------- TABS ----------------
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        root.addWidget(self.tabs, stretch=1)

        self.models_tab = ModelsTab(self)
        self.alert_phones_tab = AlertPhonesTab(self)
        self.password_tab = ChangePasswordTab(self)

        self.tabs.addTab(self.models_tab, "Models")
        self.tabs.addTab(self.alert_phones_tab, "Alert Contacts")
        self.tabs.addTab(self.password_tab, "Security")

        # ---------------- FOOTER ACTIONS ----------------
        footer = self._build_footer()
        root.addWidget(footer)

    # --------------------------------------------------
    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("HeaderFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(12)

        title = QLabel("System Settings")
        title.setObjectName("DialogTitle")

        subtitle = QLabel("Configuration & Control Panel")
        subtitle.setObjectName("MutedText")
        subtitle.setAlignment(Qt.AlignVCenter)

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(subtitle)
        layout.addStretch()

        return frame

    # --------------------------------------------------
    def _build_footer(self) -> QFrame:
        frame = QFrame()
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(12)

        layout.addStretch()

        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setProperty("role", "secondary")
        self.btn_apply.setMinimumWidth(120)

        self.btn_ok = QPushButton("OK")
        self.btn_ok.setProperty("role", "primary")
        self.btn_ok.setMinimumWidth(120)

        self.btn_close = QPushButton("Close")
        self.btn_close.setProperty("role", "secondary")
        self.btn_close.setMinimumWidth(120)

        layout.addWidget(self.btn_apply)
        layout.addWidget(self.btn_ok)
        layout.addWidget(self.btn_close)

        return frame

    # ==================================================
    # SIGNALS
    # ==================================================
    def _connect_signals(self):
        # Footer buttons
        self.btn_apply.clicked.connect(self.apply)
        self.btn_ok.clicked.connect(self.apply_and_close)
        self.btn_close.clicked.connect(self.reject)

        # Model lifecycle events
        self.models_tab.modelActivated.connect(self._on_model_changed)
        self.models_tab.modelSaved.connect(self._on_model_changed)
        self.models_tab.modelUpdated.connect(self._on_model_changed)

    # ==================================================
    # MODEL HANDLING (CENTRALIZED)
    # ==================================================
    @Slot(int)
    def _on_model_changed(self, model_id: int):
        """
        Single authoritative model activation handler
        """
        try:
            set_active_model(model_id)
            log.info("Active model updated → %s", model_id)

            self.settings_applied.emit({
                "model_id": model_id,
                "applied": True
            })

        except Exception:
            log.exception("Failed to update active model")
            QMessageBox.critical(
                self,
                "Model Activation Failed",
                "Unable to activate the selected model.\n"
                "Please check system logs."
            )

    # ==================================================
    # APPLY LOGIC
    # ==================================================
    @Slot()
    def apply(self):
        """
        Apply settings without closing dialog
        """
        try:
            if hasattr(self.models_tab, "persist_active_selection"):
                self.models_tab.persist_active_selection()

            self.settings_applied.emit({"applied": True})

            QMessageBox.information(
                self,
                "Settings Applied",
                "All changes have been applied successfully."
            )

        except Exception:
            log.exception("Settings apply failed")
            QMessageBox.critical(
                self,
                "Apply Failed",
                "Some settings could not be applied.\n"
                "Please check system logs."
            )

    @Slot()
    def apply_and_close(self):
        self.apply()
        self.accept()
