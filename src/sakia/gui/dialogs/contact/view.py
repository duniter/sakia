from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QT_TRANSLATE_NOOP, Qt, QModelIndex
from .contact_uic import Ui_ContactDialog
from duniterpy.documents.constants import pubkey_regex
import re


class ContactView(QDialog, Ui_ContactDialog):
    """
    The view of the certification component
    """

    def __init__(self, parent):
        """

        :param parent:
        """
        super().__init__(parent)
        self.setupUi(self)
        self.edit_name.textChanged.connect(self.check_name)
        self.edit_pubkey.textChanged.connect(self.check_pubkey)
        self.add_info_button.hide()
        self.check_pubkey()
        self.check_name()

    def set_table_contacts_model(self, model):
        """
        Define the table history model
        :param QAbstractItemModel model:
        :return:
        """
        self.table_contacts.setModel(model)
        self.table_contacts.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_contacts.setSortingEnabled(True)
        self.table_contacts.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_contacts.resizeRowsToContents()
        self.table_contacts.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def selected_contact_index(self):
        indexes = self.table_contacts.selectedIndexes()
        if indexes:
            return indexes[0]
        return QModelIndex()

    def check_pubkey(self):
        text = self.edit_pubkey.text()
        re_pubkey = re.compile(pubkey_regex)
        result = re_pubkey.match(text)
        if result:
            self.edit_pubkey.setStyleSheet("")
            self.button_save.setEnabled(True)
        else:
            self.edit_pubkey.setStyleSheet("border: 1px solid red")
            self.button_save.setDisabled(True)

    def check_name(self):
        text = self.edit_name.text()
        re_name = re.compile("[\w\s\d]+")
        result = re_name.match(text)
        if result:
            self.edit_name.setStyleSheet("")
            self.button_save.setEnabled(True)
        else:
            self.edit_name.setStyleSheet("border: 1px solid red")
            self.button_save.setDisabled(True)
