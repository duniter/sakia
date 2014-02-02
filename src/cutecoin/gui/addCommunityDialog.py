'''
Created on 2 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.addCommunityDialog_uic import Ui_AddCommunityDialog
from PyQt5.QtWidgets import QDialog

class AddCommunityDialog(QDialog, Ui_AddCommunityDialog):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        super(AddCommunityDialog, self).__init__()
        self.setupUi(self)

