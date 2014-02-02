'''
Created on 2 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.addAccountDialog_uic import Ui_AddAccountDialog
from PyQt5.QtWidgets import QDialog
from cutecoin.gui.addCommunityDialog import AddCommunityDialog

class AddAccountDialog(QDialog, Ui_AddAccountDialog):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(AddAccountDialog, self).__init__()
        self.setupUi(self)
        print("stiio")

    def openAddCommunityDialog(self):
        dialog = AddCommunityDialog()
        dialog.show()

