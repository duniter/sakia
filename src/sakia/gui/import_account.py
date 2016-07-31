"""
Created on 22 mai 2014

@author: inso
"""
import re
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QFileDialog

from ..tools.exceptions import Error
from ..presentation.import_account_uic import Ui_ImportAccountDialog


class ImportAccountDialog(QDialog, Ui_ImportAccountDialog):

    """
    classdocs
    """

    def __init__(self, app, parent=None):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.main_window = parent
        self.selected_file = ""
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        account_name = self.edit_name.text()
        try:
            self.app.import_account(self.selected_file, account_name)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 "{0}".format(e),
                                 QMessageBox.Ok)
            return
        QMessageBox.information(self, self.tr("Account import"),
                                self.tr("Account imported succefully !"))
        super().accept()

    def import_account(self):
        self.selected_file = QFileDialog.getOpenFileName(self,
                                          self.tr("Import an account file"),
                                          "",
                                          self.tr("All account files (*.acc)"))
        self.selected_file = self.selected_file[0]
        self.edit_file.setText(self.selected_file)
        self.check()

    def name_changed(self):
        self.check()

    def check(self):
        name = self.edit_name.text()
        if name == "":
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.label_errors.setText(self.tr("Please enter a name"))
            return
        for account in self.app.accounts:
            if name == account:
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                self.label_errors.setText(self.tr("Name already exists"))
                return
        if self.selected_file[-4:] != ".acc":
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.label_errors.setText(self.tr("File is not an account format"))
            return
        self.label_errors.setText("")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
