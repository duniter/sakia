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
        self.main_window = parent
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        name = self.edit_name.text()
        fingerprint = self.edit_fingerprint.text()
        email = self.edit_email.text()
        self.account.add_contact(Person(name, fingerprint, email))
        self.main_window.menu_contacts_list.addAction(name)
        self.close()

    def name_edited(self, new_name):
        name_ok = len(new_name) > 0
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(name_ok)

    def fingerprint_edited(self, new_fingerprint):
        pattern = re.compile("([A-Z]|[0-9])+")
        self.button_box.button(
            QDialogButtonBox.Ok).setEnabled(
            pattern.match(new_fingerprint) is not None)
