'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow
from cutecoin.gui.addAccountDialog import AddAccountDialog

class MainWindow(QMainWindow, Ui_MainWindow):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(MainWindow, self).__init__()
        self.setupUi(self)

    def openAddAccountDialog(self):
        dialog = AddAccountDialog()
        print("shoow")
        dialog.show()
        print("shoow2")