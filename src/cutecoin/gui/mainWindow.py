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


    def __init__(self, core):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.core = core

    def openAddAccountDialog(self):
        self.dialog = AddAccountDialog()
        self.dialog.setData()
        self.dialog.exec_()

    def actionAddAccount(self):
        self.core.addAccount(self.dialog.account)

    '''
    Refresh main window
    When the selected account changes, all the widgets
    in the window have to be refreshed
    '''
    def refreshMainWindow(self):
        if self.core.currentAccount != None:
            #TODO: rafraichissement de la fenetre
            pass
