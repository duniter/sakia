'''
Created on 2 févr. 2014

@author: inso
'''
import re
from PyQt5.QtWidgets import QDialog, QDialogButtonBox


from cutecoin.models.person import Person

from cutecoin.gen_resources.addContactDialog_uic import Ui_AddContactDialog

class AddContactDialog(QDialog, Ui_AddContactDialog):
    '''
    classdocs
    '''
    def __init__(self, account, parent=None):
        '''
        Constructor
        '''
        super(AddContactDialog, self).__init__()
        self.setupUi(self)
        self.account = account
        self.mainWindow = parent
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)


    def accept(self):
        name = self.edit_name.text()
        fingerprint = self.edit_fingerprint.text()
        email = self.edit_email.text()
        self.account.addContact(Person(name, fingerprint, email))
        self.mainWindow.menu_contactsList.addAction(name)
        self.close()

    def nameEdited(self, newName):
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled( len(newName) > 0 )

    def fingerprintEdited(self, newFingerprint):
        pattern = re.compile("([A-Z]|[0-9])+")
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled( pattern.match(newFingerprint) is not None )

