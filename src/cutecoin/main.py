"""
Created on 1 févr. 2014

@author: inso
"""
import signal
import sys
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
    app.load()
    app.switch_language()
    asyncio.set_event_loop(loop)
    logging.debug("Debug enabled : {0}".format(loop.get_debug()))
    with loop:
        window = MainWindow(app)
        window.showMaximized()
        loop.run_forever()
    sys.exit()
