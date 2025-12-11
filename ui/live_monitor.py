# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'live_monitor.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QListWidget,
    QListWidgetItem, QPushButton, QSizePolicy, QVBoxLayout,
    QWidget)

class Ui_LiveMonitor(object):
    def setupUi(self, LiveMonitor):
        if not LiveMonitor.objectName():
            LiveMonitor.setObjectName(u"LiveMonitor")
        LiveMonitor.resize(1920, 1000)
        self.verticalLayout = QVBoxLayout(LiveMonitor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.monitorHeader = QWidget(LiveMonitor)
        self.monitorHeader.setObjectName(u"monitorHeader")
        self.horizontalLayout = QHBoxLayout(self.monitorHeader)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.titleLabel = QLabel(self.monitorHeader)
        self.titleLabel.setObjectName(u"titleLabel")

        self.horizontalLayout.addWidget(self.titleLabel)

        self.modelInfoLabel = QLabel(self.monitorHeader)
        self.modelInfoLabel.setObjectName(u"modelInfoLabel")

        self.horizontalLayout.addWidget(self.modelInfoLabel)

        self.settingsButton = QPushButton(self.monitorHeader)
        self.settingsButton.setObjectName(u"settingsButton")

        self.horizontalLayout.addWidget(self.settingsButton)


        self.verticalLayout.addWidget(self.monitorHeader)

        self.chartContainer = QWidget(LiveMonitor)
        self.chartContainer.setObjectName(u"chartContainer")

        self.verticalLayout.addWidget(self.chartContainer)

        self.cyclesSection = QWidget(LiveMonitor)
        self.cyclesSection.setObjectName(u"cyclesSection")
        self.verticalLayout_2 = QVBoxLayout(self.cyclesSection)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.cyclesHeaderLabel = QLabel(self.cyclesSection)
        self.cyclesHeaderLabel.setObjectName(u"cyclesHeaderLabel")

        self.verticalLayout_2.addWidget(self.cyclesHeaderLabel)

        self.cyclesList = QListWidget(self.cyclesSection)
        self.cyclesList.setObjectName(u"cyclesList")

        self.verticalLayout_2.addWidget(self.cyclesList)


        self.verticalLayout.addWidget(self.cyclesSection)


        self.retranslateUi(LiveMonitor)

        QMetaObject.connectSlotsByName(LiveMonitor)
    # setupUi

    def retranslateUi(self, LiveMonitor):
        self.titleLabel.setText(QCoreApplication.translate("LiveMonitor", u"\U0001f4ca Laser QC System", None))
        self.modelInfoLabel.setText(QCoreApplication.translate("LiveMonitor", u"Model Info", None))
        self.settingsButton.setText(QCoreApplication.translate("LiveMonitor", u"\u2699\ufe0f Settings", None))
        self.cyclesHeaderLabel.setText(QCoreApplication.translate("LiveMonitor", u"\U0001f4c8 Recent Cycles", None))
        pass
    # retranslateUi

