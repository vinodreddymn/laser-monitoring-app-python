# gui/windows/settings_window.py

from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QPushButton,
    QMessageBox, QDialog, QHBoxLayout
)
from PySide6.QtCore import Signal, Slot

# local tabs (optional)
try:
    from .models_tab import ModelsTab
except Exception:
    ModelsTab = None

try:
    from .alert_phones_tab import AlertPhonesTab
except Exception:
    AlertPhonesTab = None

try:
    from .qr_settings_modal import QRSettingsModalQt
except Exception:
    QRSettingsModalQt = None

# backend helpers
from backend.models_dao import get_model_by_id, set_active_model as db_set_active_model


class SettingsWindow(QDialog):
    """
    Central settings dialog composed of multiple tabs.
    Emits settings_applied(dict) whenever Apply/OK is pressed or
    when any tab requests active model change.
    """

    settings_applied = Signal(dict)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("System Settings")
        self.setMinimumWidth(900)
        self.setMinimumHeight(640)

        self._init_ui()
        self._wire_tab_signals()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Tabs
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs, stretch=1)

        # Models
        self.models_tab = None
        if ModelsTab:
            try:
                self.models_tab = ModelsTab(self)
                self.tabs.addTab(self.models_tab, "Models")
            except Exception as e:
                print("Failed to load ModelsTab:", e)

        # Alert Phones
        self.phones_tab = None
        if AlertPhonesTab:
            try:
                self.phones_tab = AlertPhonesTab(self)
                self.tabs.addTab(self.phones_tab, "Alert Phones")
            except Exception as e:
                print("Failed to load AlertPhonesTab:", e)

        # QR Settings
        self.qr_widget = None
        if QRSettingsModalQt:
            try:
                self.qr_widget = QRSettingsModalQt(self)
                self.tabs.addTab(self.qr_widget, "QR Settings")
            except Exception as e:
                print("Failed to load QRSettingsModalQt:", e)

        # Buttons Bar
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_apply = QPushButton("Apply")
        self.btn_ok = QPushButton("OK")
        self.btn_close = QPushButton("Close")

        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_ok.clicked.connect(self.ok_and_close)
        self.btn_close.clicked.connect(self.close)

        btn_row.addWidget(self.btn_apply)
        btn_row.addWidget(self.btn_ok)
        btn_row.addWidget(self.btn_close)

        layout.addLayout(btn_row)

    # ------------------------------------------------------------------
    # Tab Signal Wiring
    # ------------------------------------------------------------------
    def _wire_tab_signals(self):
        """
        Wire tab events to unified apply logic
        Expected signals:
            modelActivated(int), modelSaved(int), modelUpdated(int)
        """
        if not self.models_tab:
            return

        # Wire if present
        mapping = {
            "modelActivated": self._on_model_activated,
            "modelSaved": self._on_model_saved,
            "modelUpdated": self._on_model_updated,
        }

        for sig_name, handler in mapping.items():
            sig = getattr(self.models_tab, sig_name, None)
            if sig:
                try:
                    sig.connect(handler)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Tab events -> apply
    # ------------------------------------------------------------------
    @Slot(int)
    def _on_model_activated(self, model_id: int):
        self._apply_model_change(model_id)

    @Slot(int)
    def _on_model_saved(self, model_id: int):
        self._apply_model_change(model_id)

    @Slot(int)
    def _on_model_updated(self, model_id: int):
        self._apply_model_change(model_id)

    # ------------------------------------------------------------------
    # Apply logic
    # ------------------------------------------------------------------
    def _collect_payload(self) -> Dict[str, Any]:
        """
        Collect all settings from tabs into a single payload
        """
        payload: Dict[str, Any] = {}

        # --- Model
        model_id = None
        lower = None
        upper = None

        # Try tab API
        try:
            if self.models_tab and hasattr(self.models_tab, "get_active_model_id"):
                model_id = self.models_tab.get_active_model_id()
        except Exception:
            pass

        # Fetch full DB info if model found
        if model_id is not None:
            m = get_model_by_id_safe(model_id)
            if m:
                lower = float(m.get("lower_limit", 0))
                upper = float(m.get("upper_limit", 0))

        payload["model_id"] = model_id
        payload["lower"] = lower or 0.0
        payload["upper"] = upper or 0.0

        # --- Phones
        phones: List[Dict[str, Any]] = []
        try:
            if self.phones_tab and hasattr(self.phones_tab, "get_all_phone_records"):
                phones = self.phones_tab.get_all_phone_records() or []
        except Exception:
            pass

        payload["alert_phones"] = phones

        # --- QR
        qr_prefix = None
        qr_counter = None

        if self.qr_widget:
            try:
                if hasattr(self.qr_widget, "get_current_values"):
                    q = self.qr_widget.get_current_values()
                    qr_prefix = q.get("qr_prefix")
                    qr_counter = q.get("qr_counter")
                else:
                    qr_prefix = getattr(self.qr_widget, "qr_prefix", None)
                    qr_counter = getattr(self.qr_widget, "qr_counter", None)
            except Exception:
                pass

        payload["qr_prefix"] = qr_prefix
        payload["qr_counter"] = qr_counter

        payload["applied"] = True
        return payload

    def _apply_model_change(self, model_id: int):
        """
        Persist active model and emit payload
        """
        if model_id is not None:
            try:
                db_set_active_model(model_id)
            except Exception:
                pass

        p = self._collect_payload()
        p["model_id"] = model_id
        self.settings_applied.emit(p)

    # ------------------------------------------------------------------
    # Button Slots
    # ------------------------------------------------------------------
    @Slot()
    def apply_settings(self):
        """
        Apply all changes but do not close dialog
        """
        # Persist active selection if models tab helps
        try:
            if self.models_tab and hasattr(self.models_tab, "persist_active_selection"):
                self.models_tab.persist_active_selection()
        except Exception:
            pass

        payload = self._collect_payload()
        mid = payload.get("model_id")
        if mid is not None:
            try:
                db_set_active_model(mid)
            except Exception:
                pass

        self.settings_applied.emit(payload)
        QMessageBox.information(self, "Settings", "Settings applied successfully.")

    @Slot()
    def ok_and_close(self):
        self.apply_settings()
        self.close()


# ----------------------------------------------------------------------
# Safe wrappers
# ----------------------------------------------------------------------
def get_model_by_id_safe(model_id: Optional[int]):
        if model_id is None:
            return None
        try:
            return get_model_by_id(model_id)
        except Exception:
            try:
                from backend.models_dao import get_model_by_id as _g
                return _g(model_id)
            except Exception:
                return None
