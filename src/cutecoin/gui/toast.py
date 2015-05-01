'''
Created on 1 mai 2015

@author: inso
'''
import sys, time
from PyQt5.QtCore import Qt, QThread
from PyQt5.QtWidgets import QMainWindow
from ..gen_resources.toast_uic import Ui_Toast

window = None   # global

class Toast(QMainWindow, Ui_Toast):
    def __init__(self, msg):
        global window               # some space outside the local stack
        window = self               # save pointer till killed to avoid GC
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setupUi(self)

        self.display.setText(msg)

        self.toastThread = ToastThread()    # start thread to remove display
        self.toastThread.finished.connect(self.toastDone)
        self.toastThread.start()
        self.show()

    def toastDone(self):
        global window
        window = None               # kill pointer to window object to close it and GC

class ToastThread(QThread):
    def __init__(self):
        QThread.__init__(self)

    def run(self):
        time.sleep(2.0)