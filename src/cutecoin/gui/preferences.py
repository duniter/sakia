'''
Created on 11 mai 2015

@author: inso
'''

from PyQt5.QtCore import QCoreApplication

from ..core.account import Account
from . import toast
from PyQt5.QtWidgets import QDialog

from ..gen_resources.preferences_uic import Ui_PreferencesDialog


class PreferencesDialog(QDialog, Ui_PreferencesDialog):

    '''
    A dialog to get password.
    '''

    def __init__(self, app):
        """
        Init instance
        :param cutecoin.core.app.Application app:   Application instance
        :return:
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.combo_account.addItem("")
        for account_name in self.app.accounts.keys():
            self.combo_account.addItem(account_name)
        self.combo_account.setCurrentText(self.app.preferences['account'])
        for ref in Account.referentials:
            self.combo_referential.addItem(QCoreApplication.translate('Account', ref[4]))
        self.combo_referential.setCurrentIndex(self.app.preferences['ref'])
        for lang in ('en_GB', 'fr_FR'):
            self.combo_language.addItem(lang)
        self.combo_language.setCurrentText(self.app.preferences['lang'])

    def accept(self):
        pref = {'account': self.combo_account.currentText(),
                'lang': self.combo_language.currentText(),
                'ref': self.combo_referential.currentIndex()}
        self.app.save_preferences(pref)
        toast.display(self.tr("Preferences"),
                      self.tr("A restart is needed to apply your new preferences."))
        super().accept()

    def reject(self):
        super().reject()


