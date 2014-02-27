'''
Created on 2 févr. 2014

@author: inso
'''
import logging

from PyQt5.QtWidgets import QDialog, QDialogButtonBox


from cutecoin.models.person import Person

from cutecoin.gen_resources.addContactDialog_uic import Ui_AddContactDialog

class AddContactDialog(QDialog, Ui_AddContactDialog):
    '''
    classdocs
    '''
    def __init__(self, account):
        '''
        Constructor
        '''
        super(AddContactDialog, self).__init__()
        self.setupUi(self)


    def accept(self):
        #TODO: Add a contact on acceptance
        pass

    def nameEdited(self, newName):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled( len(newName) > 0 )

    def fingerprintEdited(self, newFingerprint):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled( len(newFingerprint) == 32 )

