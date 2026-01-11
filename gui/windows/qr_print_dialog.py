import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTabWidget

from gui.windows.pending_qr_print_window import PendingQRPrintTab
from gui.windows.qr_search_print_tab import QRSearchPrintTab
from gui.styles.app_styles import apply_base_dialog_style

log = logging.getLogger(__name__)


class QRPrintDialog(QDialog):
    """
    QR Label Printing Dialog

    Tabs:
    - Pending QR Labels
    - Search & Print QR
    """

    WIDTH = 1300
    HEIGHT = 900

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("QR Label Printing")
        self.setModal(True)
        self.setMinimumSize(self.WIDTH, self.HEIGHT)

        self._build_ui()
        apply_base_dialog_style(self)

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.pending_tab = PendingQRPrintTab(self)
        self.search_tab = QRSearchPrintTab(self)

        self.tabs.addTab(self.pending_tab, "Pending QR Labels")
        self.tabs.addTab(self.search_tab, "Search and Print QR")

        self.tabs.setCurrentIndex(0)
