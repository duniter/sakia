'''
Created on 2 févr. 2014

@author: inso
'''
import re
import logging

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from ..core.person import Person
from ..tools.exceptions import ContactAlreadyExists
from ..gen_resources.contact_uic import Ui_ConfigureContactDialog


class ConfigureContactDialog(QDialog, Ui_ConfigureContactDialog):

    '''
    classdocs
    '''

    def __init__(self, account, parent=None, contact=None, index_edit=None):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.main_window = parent
        self.index_edit = index_edit
        if type(contact) is Person:
            self.contact = {'name': contact.name,
                            'pubkey': contact.pubkey}
        elif type(contact) is dict:
            self.contact = contact

        if index_edit is not None:
            self.contact = account.contacts[index_edit]
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        if self.contact:
            self.edit_name.setText(self.contact['name'])
            self.edit_pubkey.setText(self.contact['pubkey'])

    def accept(self):
        name = self.edit_name.text()
        pubkey = self.edit_pubkey.text()
        if self.index_edit is not None:
            self.account.contacts[self.index_edit] = {'name': name,
                          'pubkey': pubkey}
            logging.debug(self.contact)
        else:
            try:
                self.account.add_contact({'name': name,
                                          'pubkey': pubkey})
            except ContactAlreadyExists as e:
                QMessageBox.critical(self, "Contact already exists",
                            str(e),
                            QMessageBox.Ok)
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
