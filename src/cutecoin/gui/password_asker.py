'''
Created on 24 dec. 2014

@author: inso
'''

import logging

from PyQt5.QtWidgets import QDialog, QMessageBox

from ..gen_resources.password_asker_uic import Ui_PasswordAskerDialog


class PasswordAskerDialog(QDialog, Ui_PasswordAskerDialog):

    '''
    A dialog to get password.
    '''

    def __init__(self, account):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.password = ""
        self.remember = False

    def exec_(self):
        if not self.remember:
            super().exec_()
            pwd = self.password
            if not self.remember:
                self.password = ""
            return pwd
        else:
            self.setResult(QDialog.Accepted)
            return self.password

    def accept(self):
        password = self.edit_password.text()
        if self.account.check_password(password):
            self.remember = self.check_remember.isChecked()
            self.password = password
            self.edit_password.setText("")
            logging.debug("Password is valid")
            super().accept()
        else:
            QMessageBox.warning(self, "Failed to get private key",
                                "Wrong password typed. Cannot open the private key",
                                QMessageBox.Ok)

    def reject(self):
        self.edit_password.setText("")
        logging.debug("Cancelled")
        self.setResult(QDialog.Accepted)
        self.password = ""
        super().reject()