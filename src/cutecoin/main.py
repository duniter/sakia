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
    if getattr(sys, 'frozen', False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
        os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(datadir, "DigiCertHighAssuranceEVRootCA.crt")
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(datadir,
                                                        "res", "certs",
                                                        "DigiCertHighAssuranceEVRootCA.crt")

    cutecoin = QApplication(sys.argv)
    app = Application(sys.argv)
    QLocale.setDefault(QLocale("en_GB"))
    window = MainWindow(app)
    window.show()
    sys.exit(cutecoin.exec_())
    pass
