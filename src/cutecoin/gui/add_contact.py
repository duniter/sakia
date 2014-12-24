'''
Created on 2 févr. 2014

@author: inso
'''
import re
from PyQt5.QtWidgets import QDialog, QDialogButtonBox


from cutecoin.core.person import Person

from cutecoin.gen_resources.add_contact_uic import Ui_AddContactDialog


class AddContactDialog(QDialog, Ui_AddContactDialog):

    '''
    classdocs
    '''

    def __init__(self, account, parent=None):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.main_window = parent
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        name = self.edit_name.text()
        pubkey = self.edit_pubkey.text()
        self.account.add_contact(Person(name, pubkey))
        self.main_window.menu_contacts_list.addAction(name)
        self.main_window.app.save(self.account)
        self.close()

    def name_edited(self, new_name):
        name_ok = len(new_name) > 0
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(name_ok)

    def pubkey_edited(self, new_pubkey):
        pattern = re.compile("([1-9A-Za-z][^OIl]{42,45})")
        self.button_box.button(
            QDialogButtonBox.Ok).setEnabled(
            pattern.match(new_pubkey)is not None)
