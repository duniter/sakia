from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QT_TRANSLATE_NOOP, Qt, QModelIndex
from .contact_uic import Ui_ContactDialog


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
