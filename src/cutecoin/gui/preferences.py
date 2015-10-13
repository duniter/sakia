"""
Created on 11 mai 2015

@author: inso
"""

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QDialog

from ..core import money
from ..gen_resources.preferences_uic import Ui_PreferencesDialog


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
        for ref in money.Referentials:
            self.combo_referential.addItem(QCoreApplication.translate('Account', ref.translated_name()))
        self.combo_referential.setCurrentIndex(self.app.preferences['ref'])
        for lang in ('en_GB', 'fr_FR'):
            self.combo_language.addItem(lang)
        self.combo_language.setCurrentText(self.app.preferences.get('lang', 'en_US'))
        self.checkbox_expertmode.setChecked(self.app.preferences.get('expert_mode', False))
        self.checkbox_maximize.setChecked(self.app.preferences.get('maximized', False))
        self.checkbox_notifications.setChecked(self.app.preferences.get('notifications', True))
        self.checkbox_international_system.setChecked(self.app.preferences.get('international_system_of_units', True))
        self.spinbox_digits_comma.setValue(self.app.preferences.get('digits_after_comma', 2))
        self.spinbox_digits_comma.setMaximum(12)
        self.spinbox_digits_comma.setMinimum(1)
        self.button_app.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.button_display.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.button_network.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))

        self.checkbox_proxy.setChecked(self.app.preferences.get('enable_proxy', False))
        self.spinbox_proxy_port.setEnabled(self.checkbox_proxy.isChecked())
        self.edit_proxy_address.setEnabled(self.checkbox_proxy.isChecked())
        self.checkbox_proxy.stateChanged.connect(self.handle_proxy_change)

        self.spinbox_proxy_port.setValue(self.app.preferences.get('proxy_port', 8080))
        self.spinbox_proxy_port.setMinimum(0)
        self.spinbox_proxy_port.setMaximum(55636)
        self.edit_proxy_address.setText(self.app.preferences.get('proxy_address', ""))

    def handle_proxy_change(self):
        self.spinbox_proxy_port.setEnabled(self.checkbox_proxy.isChecked())
        self.edit_proxy_address.setEnabled(self.checkbox_proxy.isChecked())

    def accept(self):
        pref = {'account': self.combo_account.currentText(),
                'lang': self.combo_language.currentText(),
                'ref': self.combo_referential.currentIndex(),
                'expert_mode': self.checkbox_expertmode.isChecked(),
                'maximized': self.checkbox_maximize.isChecked(),
                'digits_after_comma': self.spinbox_digits_comma.value(),
                'notifications': self.checkbox_notifications.isChecked(),
                'enable_proxy': self.checkbox_proxy.isChecked(),
                'proxy_address': self.edit_proxy_address.text(),
                'proxy_port': self.spinbox_proxy_port.value(),
                'international_system_of_units': self.checkbox_international_system.isChecked(),
                'auto_refresh': self.checkbox_auto_refresh.isChecked()}
        self.app.save_preferences(pref)
      # change UI translation
        self.app.switch_language()
        super().accept()

    def reject(self):
        super().reject()


