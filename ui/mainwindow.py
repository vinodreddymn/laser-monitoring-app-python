# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QSizePolicy, QStackedWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1920, 1080)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.header = QWidget(self.centralwidget)
        self.header.setObjectName(u"header")
        self.horizontalLayout = QHBoxLayout(self.header)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.dateTimeLabel = QLabel(self.header)
        self.dateTimeLabel.setObjectName(u"dateTimeLabel")

        self.horizontalLayout.addWidget(self.dateTimeLabel)


        self.verticalLayout.addWidget(self.header)

        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.setObjectName(u"stackedWidget")
        self.livePage = QWidget()
        self.livePage.setObjectName(u"livePage")
        self.stackedWidget.addWidget(self.livePage)
        self.settingsPage = QWidget()
        self.settingsPage.setObjectName(u"settingsPage")
        self.stackedWidget.addWidget(self.settingsPage)

        self.verticalLayout.addWidget(self.stackedWidget)

        self.footer = QWidget(self.centralwidget)
        self.footer.setObjectName(u"footer")
        self.horizontalLayout_2 = QHBoxLayout(self.footer)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.gsmLabel = QLabel(self.footer)
        self.gsmLabel.setObjectName(u"gsmLabel")

        self.horizontalLayout_2.addWidget(self.gsmLabel)

        self.plcLabel = QLabel(self.footer)
        self.plcLabel.setObjectName(u"plcLabel")

        self.horizontalLayout_2.addWidget(self.plcLabel)


        self.verticalLayout.addWidget(self.footer)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Pneumatic QC", None))
        self.dateTimeLabel.setText(QCoreApplication.translate("MainWindow", u"Current Date/Time", None))
        self.gsmLabel.setText(QCoreApplication.translate("MainWindow", u"GSM Status", None))
        self.plcLabel.setText(QCoreApplication.translate("MainWindow", u"PLC Status", None))
    # retranslateUi

