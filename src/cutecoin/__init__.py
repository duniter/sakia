'''
Created on 1 févr. 2014

@author: inso
'''
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from cutecoin.gui.mainWindow import MainWindow
from cutecoin.core.app import Application


if __name__ == '__main__':
    cutecoin = QApplication(sys.argv)
    app = Application(sys.argv)
    window = MainWindow(app)
    window.show()
    sys.exit(cutecoin.exec_())
    pass
