"""
Created on 2 févr. 2014

@author: inso
"""
import re
import logging

from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from ..core.registry import IdentitiesRegistry
from ..tools.exceptions import ContactAlreadyExists
from ..gen_resources.contact_uic import Ui_ConfigureContactDialog


class ConfigureContactDialog(QDialog, Ui_ConfigureContactDialog):

    """
    classdocs
    """

    def __init__(self, app, account, parent=None, contact=None, index_edit=None):
        """
        Open the dialog to create a new contact
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account
        :param PyQt5.QtWidgets.QWidget parent: the parent widget
        :param dict contact: the contact with a key 'name' and a key 'pubkey'
        :param int index_edit: the index of the edited contact in the account contacts list
        :return:
        """
        super().__init__(parent)
        self.setupUi(self)
        self.app = app
        self.account = account
        self.index_edit = index_edit
        self.contact = contact

        if index_edit is not None:
            self.contact = account.contacts[index_edit]
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

        if self.contact:
            self.edit_name.setText(self.contact['name'])
            self.edit_pubkey.setText(self.contact['pubkey'])

    @classmethod
    def from_identity(cls, app, parent, account, identity):
        contact = {
            'name': identity.uid,
            'pubkey': identity.pubkey
        }
        return ConfigureContactDialog(app, account, parent, contact)

    @classmethod
    def new_contact(cls, app, account, parent):
        """
        Open the dialog to create a new contact
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account
        :param PyQt5.QtWidgets.QWidget parent: the parent widget
        :return:
        """
        return ConfigureContactDialog(app, account, parent)

    @classmethod
    def edit_contact(cls, app, account, parent, index):
        return ConfigureContactDialog(app, account, parent, None, index)

    def accept(self):
        name = self.edit_name.text()
        pubkey = self.edit_pubkey.text()
        if self.index_edit is not None:
            self.account.edit_contact(self.index_edit, {'name': name,
                          'pubkey': pubkey})
            logging.debug(self.contact)
        else:
            try:
                self.account.add_contact({'name': name,
                                          'pubkey': pubkey})
            except ContactAlreadyExists as e:
                QMessageBox.critical(self, self.tr("Contact already exists"),
                            str(e),
                            QMessageBox.Ok)
        self.app.save(self.account)
        super().accept()

    def name_edited(self, new_name):
        name_ok = len(new_name) > 0
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(name_ok)

    def pubkey_edited(self, new_pubkey):
        pattern = re.compile("([1-9A-Za-z][^OIl]{42,45})")
        self.button_box.button(
            QDialogButtonBox.Ok).setEnabled(
            pattern.match(new_pubkey)is not None)
