"""
Created on 1 févr. 2014

@author: inso
"""
import signal
import sys
import os
import logging
import asyncio

from quamash import QEventLoop
from PyQt5.QtWidgets import QApplication
from cutecoin.gui.mainwindow import MainWindow
from cutecoin.core.app import Application

if __name__ == '__main__':
    # activate ctrl-c interrupt
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    cutecoin = QApplication(sys.argv)
    loop = QEventLoop(cutecoin)
    app = Application(sys.argv, cutecoin, loop)
    asyncio.set_event_loop(loop)
    with loop:
        window = MainWindow(app)
        window.showMaximized()
        loop.run_forever()
    sys.exit()
