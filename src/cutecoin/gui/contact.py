'''
Created on 2 févr. 2014

@author: inso
'''
import re
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from ..core.person import Person
from ..tools.exceptions import ContactAlreadyExists
from ..gen_resources.contact_uic import Ui_ConfigureContactDialog


class ConfigureContactDialog(QDialog, Ui_ConfigureContactDialog):

    '''
    classdocs
    '''

    def __init__(self, account, parent=None, contact=None, edit=False):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.main_window = parent
        self.contact = contact
        if contact:
            self.edit_name.setText(contact.name)
            self.edit_pubkey.setText(contact.pubkey)
        if edit:
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        name = self.edit_name.text()
        pubkey = self.edit_pubkey.text()
        if self.contact:
            self.contact.name = name
            self.contact.pubkey = pubkey
        else:
            try:
                self.account.add_contact(Person(name, pubkey))
            except ContactAlreadyExists as e:
                QMessageBox.critical(self, "Contact already exists",
                            str(e),
                            QMessageBox.Ok)
                return
        self.main_window.app.save(self.account)
        super().accept()

    def name_edited(self, new_name):
        name_ok = len(new_name) > 0
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(name_ok)

    def pubkey_edited(self, new_pubkey):
        pattern = re.compile("([1-9A-Za-z][^OIl]{42,45})")
        self.button_box.button(
            QDialogButtonBox.Ok).setEnabled(
            pattern.match(new_pubkey)is not None)
