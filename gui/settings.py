# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'settings.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QHeaderView, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_Settings(object):
    def setupUi(self, Settings):
        if not Settings.objectName():
            Settings.setObjectName(u"Settings")
        Settings.resize(1920, 1000)
        self.verticalLayout = QVBoxLayout(Settings)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.tabWidget = QTabWidget(Settings)
        self.tabWidget.setObjectName(u"tabWidget")
        self.modelsTab = QWidget()
        self.modelsTab.setObjectName(u"modelsTab")
        self.verticalLayout_2 = QVBoxLayout(self.modelsTab)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.modelsTable = QTableWidget(self.modelsTab)
        if (self.modelsTable.columnCount() < 4):
            self.modelsTable.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.modelsTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.modelsTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.modelsTable.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.modelsTable.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.modelsTable.setObjectName(u"modelsTable")

        self.verticalLayout_2.addWidget(self.modelsTable)

        self.addModelButton = QPushButton(self.modelsTab)
        self.addModelButton.setObjectName(u"addModelButton")

        self.verticalLayout_2.addWidget(self.addModelButton)

        self.tabWidget.addTab(self.modelsTab, "")
        self.phonesTab = QWidget()
        self.phonesTab.setObjectName(u"phonesTab")
        self.verticalLayout_3 = QVBoxLayout(self.phonesTab)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.modelComboBox = QComboBox(self.phonesTab)
        self.modelComboBox.setObjectName(u"modelComboBox")

        self.verticalLayout_3.addWidget(self.modelComboBox)

        self.phonesTable = QTableWidget(self.phonesTab)
        if (self.phonesTable.columnCount() < 2):
            self.phonesTable.setColumnCount(2)
        __qtablewidgetitem4 = QTableWidgetItem()
        self.phonesTable.setHorizontalHeaderItem(0, __qtablewidgetitem4)
        __qtablewidgetitem5 = QTableWidgetItem()
        self.phonesTable.setHorizontalHeaderItem(1, __qtablewidgetitem5)
        self.phonesTable.setObjectName(u"phonesTable")

        self.verticalLayout_3.addWidget(self.phonesTable)

        self.newPhoneEdit = QLineEdit(self.phonesTab)
        self.newPhoneEdit.setObjectName(u"newPhoneEdit")

        self.verticalLayout_3.addWidget(self.newPhoneEdit)

        self.addPhoneButton = QPushButton(self.phonesTab)
        self.addPhoneButton.setObjectName(u"addPhoneButton")

        self.verticalLayout_3.addWidget(self.addPhoneButton)

        self.tabWidget.addTab(self.phonesTab, "")
        self.qrTab = QWidget()
        self.qrTab.setObjectName(u"qrTab")
        self.verticalLayout_4 = QVBoxLayout(self.qrTab)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.qrPreviewLabel = QLabel(self.qrTab)
        self.qrPreviewLabel.setObjectName(u"qrPreviewLabel")

        self.verticalLayout_4.addWidget(self.qrPreviewLabel)

        self.qrPrefixEdit = QLineEdit(self.qrTab)
        self.qrPrefixEdit.setObjectName(u"qrPrefixEdit")

        self.verticalLayout_4.addWidget(self.qrPrefixEdit)

        self.qrCounterSpin = QSpinBox(self.qrTab)
        self.qrCounterSpin.setObjectName(u"qrCounterSpin")

        self.verticalLayout_4.addWidget(self.qrCounterSpin)

        self.saveQrButton = QPushButton(self.qrTab)
        self.saveQrButton.setObjectName(u"saveQrButton")

        self.verticalLayout_4.addWidget(self.saveQrButton)

        self.tabWidget.addTab(self.qrTab, "")

        self.verticalLayout.addWidget(self.tabWidget)

        self.backButton = QPushButton(Settings)
        self.backButton.setObjectName(u"backButton")

        self.verticalLayout.addWidget(self.backButton)


        self.retranslateUi(Settings)

        QMetaObject.connectSlotsByName(Settings)
    # setupUi

    def retranslateUi(self, Settings):
        ___qtablewidgetitem = self.modelsTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Settings", u"Name", None));
        ___qtablewidgetitem1 = self.modelsTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Settings", u"Lower Limit", None));
        ___qtablewidgetitem2 = self.modelsTable.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("Settings", u"Upper Limit", None));
        ___qtablewidgetitem3 = self.modelsTable.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("Settings", u"Actions", None));
        self.addModelButton.setText(QCoreApplication.translate("Settings", u"Add Model", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.modelsTab), QCoreApplication.translate("Settings", u"Models", None))
        ___qtablewidgetitem4 = self.phonesTable.horizontalHeaderItem(0)
        ___qtablewidgetitem4.setText(QCoreApplication.translate("Settings", u"Phone Number", None));
        ___qtablewidgetitem5 = self.phonesTable.horizontalHeaderItem(1)
        ___qtablewidgetitem5.setText(QCoreApplication.translate("Settings", u"Actions", None));
        self.addPhoneButton.setText(QCoreApplication.translate("Settings", u"Add Phone", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.phonesTab), QCoreApplication.translate("Settings", u"Alert Phones", None))
        self.qrPreviewLabel.setText(QCoreApplication.translate("Settings", u"QR Preview", None))
        self.saveQrButton.setText(QCoreApplication.translate("Settings", u"Save QR Settings", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.qrTab), QCoreApplication.translate("Settings", u"QR Settings", None))
        self.backButton.setText(QCoreApplication.translate("Settings", u"Back to Live", None))
        pass
    # retranslateUi

