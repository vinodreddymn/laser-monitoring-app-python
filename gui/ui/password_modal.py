# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'password_modal.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSplitter,
    QWidget)

class Ui_PasswordModal(object):
    def setupUi(self, PasswordModal):
        if not PasswordModal.objectName():
            PasswordModal.setObjectName(u"PasswordModal")
        PasswordModal.resize(483, 426)
        PasswordModal.setModal(True)
        self.splitter = QSplitter(PasswordModal)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setGeometry(QRect(9, 9, 361, 301))
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.label = QLabel(self.splitter)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(18)
        self.label.setFont(font)
        self.splitter.addWidget(self.label)
        self.passwordEdit = QLineEdit(self.splitter)
        self.passwordEdit.setObjectName(u"passwordEdit")
        self.passwordEdit.setEchoMode(QLineEdit.EchoMode.Password)
        self.splitter.addWidget(self.passwordEdit)
        self.widget = QWidget(self.splitter)
        self.widget.setObjectName(u"widget")
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.cancelBtn = QPushButton(self.widget)
        self.cancelBtn.setObjectName(u"cancelBtn")

        self.horizontalLayout.addWidget(self.cancelBtn)

        self.okBtn = QPushButton(self.widget)
        self.okBtn.setObjectName(u"okBtn")

        self.horizontalLayout.addWidget(self.okBtn)

        self.splitter.addWidget(self.widget)

        self.retranslateUi(PasswordModal)

        QMetaObject.connectSlotsByName(PasswordModal)
    # setupUi

    def retranslateUi(self, PasswordModal):
        PasswordModal.setWindowTitle(QCoreApplication.translate("PasswordModal", u"Settings Access", None))
        self.label.setText(QCoreApplication.translate("PasswordModal", u"Enter password to access settings:", None))
        self.passwordEdit.setPlaceholderText(QCoreApplication.translate("PasswordModal", u"Password", None))
        self.cancelBtn.setText(QCoreApplication.translate("PasswordModal", u"Cancel", None))
        self.okBtn.setText(QCoreApplication.translate("PasswordModal", u"Unlock", None))
    # retranslateUi

