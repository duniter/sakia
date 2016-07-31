"""
Created on 24 dec. 2014

@author: inso
"""

import logging
import re
import asyncio
from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QDialog, QMessageBox

from ..presentation.password_asker_uic import Ui_PasswordAskerDialog


class PasswordAskerDialog(QDialog, Ui_PasswordAskerDialog):

    """
    A dialog to get password.
    """

    def __init__(self, account):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.password = ""
        self.remember = False

    def change_account(self, account):
        self.remember = False
        self.password = ""
        self.account = account

    def async_exec(self):
        future = asyncio.Future()
        if not self.remember:
            def future_show():
                pwd = self.password
                if not self.remember:
                    self.password = ""
                self.finished.disconnect(future_show)
                future.set_result(pwd)
            self.open()
            self.finished.connect(future_show)
        else:
            self.setResult(QDialog.Accepted)
            future.set_result(self.password)
        return future

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

        if detect_non_printable(password):
            QMessageBox.warning(self, self.tr("Bad password"),
                                self.tr("Non printable characters in password"),
                                QMessageBox.Ok)
            return False

        if not self.account.check_password(password):
            QMessageBox.warning(self, self.tr("Failed to get private key"),
                                self.tr("Wrong password typed. Cannot open the private key"),
                                QMessageBox.Ok)
            return False

        self.remember = self.check_remember.isChecked()
        self.password = password
        self.edit_password.setText("")
        logging.debug("Password is valid")
        super().accept()

    def reject(self):
        self.edit_password.setText("")
        logging.debug("Cancelled")
        self.setResult(QDialog.Accepted)
        self.password = ""
        super().reject()

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
        return super(PasswordAskerDialog, self).changeEvent(event)


def detect_non_printable(data):
    control_chars = ''.join(map(chr, list(range(0, 32)) + list(range(127, 160))))
    control_char_re = re.compile('[%s]' % re.escape(control_chars))
    if control_char_re.search(data):
        return True
