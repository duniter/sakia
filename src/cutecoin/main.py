"""
Created on 1 févr. 2014

@author: inso
"""
import signal
import sys
import os

from PyQt5.QtWidgets import QApplication, QDialog
from cutecoin.gui.mainWindow import MainWindow
from cutecoin.core.app import Application


if __name__ == '__main__':
    # activate ctrl-c interrupt
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    cutecoin = QApplication(sys.argv)
    app = Application(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(cutecoin.exec_())
    pass
