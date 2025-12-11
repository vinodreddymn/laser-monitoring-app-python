# gui/password_modal.py
from PySide6.QtWidgets import QDialog
from PySide6.QtCore import Qt
from .ui.password_modal import Ui_PasswordModal  # ← generated from .ui file


class PasswordModal(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_PasswordModal()
        self.ui.setupUi(self)

        # Connect buttons
        self.ui.okBtn.clicked.connect(self.accept)
        self.ui.cancelBtn.clicked.connect(self.reject)

        # Focus password field
        self.ui.passwordEdit.setFocus()
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)

    def get_password(self):
        return self.ui.passwordEdit.text()