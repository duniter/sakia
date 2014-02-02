'''
Created on 1 févr. 2014

@author: inso
'''
import sys
from PyQt5.QtWidgets import QApplication, QDialog
from cutecoin.gui.mainWindow import MainWindow
from cutecoin.models.account import Account

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
    pass