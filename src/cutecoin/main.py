"""
Created on 1 févr. 2014

@author: inso
"""
import signal
import sys
import os

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QLocale
from cutecoin.gui.mainwindow import MainWindow
from cutecoin.core.app import Application

if __name__ == '__main__':
    # activate ctrl-c interrupt
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    cutecoin = QApplication(sys.argv)
    app = Application(sys.argv)
    QLocale.setDefault(QLocale("en_GB"))
    window = MainWindow(app)
    window.showMaximized()
    sys.exit(cutecoin.exec_())
    pass
