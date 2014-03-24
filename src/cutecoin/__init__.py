'''
Created on 1 févr. 2014

@author: inso
'''
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from cutecoin.gui.mainWindow import MainWindow
from cutecoin.core import Core

#TODO: Rename all functions to match python style

if __name__ == '__main__':
    app = QApplication(sys.argv)
    core = Core(sys.argv)
    window = MainWindow(core)
    window.show()
    sys.exit(app.exec_())
    pass
