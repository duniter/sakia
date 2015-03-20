'''
Created on 20 mars 2015

@author: inso
'''

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal


class Watcher(QObject):
    watching_stopped = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    @pyqtSlot()
    def watch(self):
        pass

    @pyqtSlot()
    def stop(self):
        pass
