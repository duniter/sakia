'''
Created on 22 mai 2014

@author: inso
'''
from ucoinpy.key import SigningKey

import re
import logging
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QProgressDialog
from PyQt5.QtCore import QThread, pyqtSignal

from cutecoin.gen_resources.generateKeyDialog_uic import Ui_GenerateKeyDialog


class TaskGenKey(QThread):
    taskFinished = pyqtSignal()

    def run(self):
        self.key = self.account.gpg.gen_key(self.input_data)
        self.taskFinished.emit()


class GenerateAccountKeyDialog(QDialog, Ui_GenerateKeyDialog):

    '''
    classdocs
    '''

    def __init__(self, account, parent=None):
        '''
        Constructor
        '''
        super(GenerateAccountKeyDialog, self).__init__()
        self.setupUi(self)
        self.account = account
        self.main_window = parent
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def accept(self):
        name = self.edit_name.text()
        password = self.edit_password.text()
        password_repeat = self.edit_password_repeat.text()
        salt = self.edit_email.text()

    def gen_finished(self):
        self.progress_dialog.close()
        self.account.key = SigningKey(self.salt, self.password)

        logging.debug("Key generated : " + self.account.keyid)

        QMessageBox.information(self, "Key generation", "Key " +
                                self.account.key.pubkey + " has been generated",
                        QMessageBox.Ok)
        self.main_window.label_pubkey.setText("Key : " + self.account.key.public_key)
        self.main_window.button_next.setEnabled(True)
        self.close()

    def check(self):
        if len(self.edit_password.text()) < 8:
            self.label_errors.setText("Please enter a password with more than 8 characters")
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        elif self.edit_password.text() != self.edit_password_repeat.text():
            self.label_errors.setText("Passwords do not match")
            self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
            return
        else:
            pattern = re.compile("([A-Za-z-.]+ )([A-Za-z-.]+( )*)+")
            if not pattern.match(self.edit_name.text()):
                self.label_errors.setText("Please enter your name and family name.")
                self.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
                return

        self.label_errors.setText("")
        self.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

