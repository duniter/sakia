'''
Created on 11 mai 2015

@author: inso
'''

import logging

from ..core.account import Account
from PyQt5.QtWidgets import QDialog

from ..gen_resources.preferences_uic import Ui_PreferencesDialog


class PreferencesDialog(QDialog, Ui_PreferencesDialog):

    '''
    A dialog to get password.
    '''

    def __init__(self, app):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.combo_account.addItem("")
        for account_name in self.app.accounts.keys():
            self.combo_account.addItem(account_name)
        self.combo_account.setCurrentText(self.app.preferences['account'])
        for ref in Account.referentials:
            self.combo_referential.addItem(ref)
        for lang in ('en_GB', 'fr_FR'):
            self.combo_language.addItem(lang)

    def accept(self):
        pref = {'account': self.combo_account.currentText(),
                'lang': self.combo_language.currentText(),
                'ref': self.combo_referential.currentText()}
        self.app.save_preferences(pref)
        super().accept()

    def reject(self):
        super().reject()


