'''
Created on 22 mai 2014

@author: inso
'''
import re
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QErrorMessage, QFileDialog

from cutecoin.tools.exceptions import Error
from cutecoin.gen_resources.importAccountDialog_uic import Ui_ImportAccountDialog


class ImportAccountDialog(QDialog, Ui_ImportAccountDialog):

    '''
    classdocs
    '''

    def __init__(self, core, parent=None):
        '''
        Constructor
        '''
        super(ImportAccountDialog, self).__init__()
        self.setupUi(self)
        self.core = core
        self.main_window = parent
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        account_name = self.edit_name.text()
        try:
            self.core.import_account(self.selected_file, account_name)
        except Error as e:
            QErrorMessage(self).showMessage(e.message)
            return
        QMessageBox.information(self, "Account import",
                                "Account imported succefully !")
        self.accepted.emit()
        self.close()

    def import_account(self):
        self.selected_file = QFileDialog.getOpenFileName(self,
                                          "Import an account file",
                                          "",
                                          "All account files (*.acc)")
        self.selected_file = self.selected_file[0]
        self.edit_file.setText(self.selected_file)
        self.check()

    def name_changed(self):
        self.check()

    def check(self):
        name = self.edit_name.text()
        if name == "":
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.label_errors.setText("Please enter a name")
            return
        for account in self.core.accounts:
            if name == account.name:
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                self.label_errors.setText("Name already exists")
                return
        if self.selected_file[-4:] != ".acc":
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            self.label_errors.setText("File is not an account format")
            return
        self.label_errors.setText("")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
