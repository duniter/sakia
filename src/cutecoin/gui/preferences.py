"""
Created on 11 mai 2015

@author: inso
"""

from PyQt5.QtCore import QCoreApplication

from ..core.account import Account
from . import toast
from PyQt5.QtWidgets import QDialog
from PyQt5.QtGui import QIcon

from ..gen_resources.preferences_uic import Ui_PreferencesDialog
import icons_rc


class PreferencesDialog(QDialog, Ui_PreferencesDialog):

    """
    A dialog to get password.
    """

    def __init__(self, app):
        """
        Constructor
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
        self.checkbox_expertmode.setChecked(self.app.preferences['expert_mode'])
        self.checkbox_maximize.setChecked(self.app.preferences['maximized'])
        self.spinbox_digits_comma.setValue(self.app.preferences['digits_after_comma'])
        self.spinbox_digits_comma.setMaximum(12)
        self.spinbox_digits_comma.setMinimum(1)
        self.button_app.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.button_display.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.button_network.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))

    def accept(self):
        pref = {'account': self.combo_account.currentText(),
                'lang': self.combo_language.currentText(),
                'ref': self.combo_referential.currentIndex(),
                'expert_mode': self.checkbox_expertmode.isChecked(),
                'maximized': self.checkbox_maximize.isChecked(),
                'digits_after_comma': self.spinbox_digits_comma.value()}
        self.app.save_preferences(pref)
        toast.display(self.tr("Preferences"),
                      self.tr("A restart is needed to apply your new preferences."))
        super().accept()

    def reject(self):
        super().reject()


