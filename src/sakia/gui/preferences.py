"""
Created on 11 mai 2015

@author: inso
"""

from PyQt5.QtCore import QCoreApplication
from PyQt5.QtWidgets import QDialog

from sakia import money
from sakia.data.entities import UserParameters
from .preferences_uic import Ui_PreferencesDialog


class PreferencesDialog(QDialog, Ui_PreferencesDialog):

    """
    A dialog to get password.
    """

    def __init__(self, app):
        """
        Constructor

        :param sakia.app.Application app:
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        for ref in money.Referentials:
            self.combo_referential.addItem(QCoreApplication.translate('Account', ref.translated_name()))
        self.combo_referential.setCurrentIndex(self.app.parameters.referential)
        for lang in ('en_US', 'fr_FR', 'de_DE', 'es_ES', 'it_IT', 'pl_PL', 'pt_BR', 'ru_RU'):
            self.combo_language.addItem(lang)
        self.combo_language.setCurrentText(self.app.parameters.lang)
        self.checkbox_expertmode.setChecked(self.app.parameters.expert_mode)
        self.checkbox_maximize.setChecked(self.app.parameters.maximized)
        self.checkbox_notifications.setChecked(self.app.parameters.notifications)
        self.spinbox_digits_comma.setValue(self.app.parameters.digits_after_comma)
        self.spinbox_digits_comma.setMaximum(12)
        self.spinbox_digits_comma.setMinimum(1)
        self.button_app.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(0))
        self.button_display.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(1))
        self.button_network.clicked.connect(lambda: self.stackedWidget.setCurrentIndex(2))

        self.checkbox_proxy.setChecked(self.app.parameters.enable_proxy)
        self.spinbox_proxy_port.setEnabled(self.checkbox_proxy.isChecked())
        self.edit_proxy_address.setEnabled(self.checkbox_proxy.isChecked())
        self.checkbox_proxy.stateChanged.connect(self.handle_proxy_change)

        self.spinbox_proxy_port.setMinimum(0)
        self.spinbox_proxy_port.setMaximum(55636)
        self.spinbox_proxy_port.setValue(self.app.parameters.proxy_port)
        self.edit_proxy_address.setText(self.app.parameters.proxy_address)

    def handle_proxy_change(self):
        self.spinbox_proxy_port.setEnabled(self.checkbox_proxy.isChecked())
        self.edit_proxy_address.setEnabled(self.checkbox_proxy.isChecked())

    def accept(self):
        parameters = UserParameters(lang=self.combo_language.currentText(),
                                    referential=self.combo_referential.currentIndex(),
                                    expert_mode=self.checkbox_expertmode.isChecked(),
                                    maximized=self.checkbox_maximize.isChecked(),
                                    digits_after_comma=self.spinbox_digits_comma.value(),
                                    notifications=self.checkbox_notifications.isChecked(),
                                    enable_proxy=self.checkbox_proxy.isChecked(),
                                    proxy_address=self.edit_proxy_address.text(),
                                    proxy_port=self.spinbox_proxy_port.value())
        self.app.save_parameters(parameters)
      # change UI translation
        self.app.switch_language()
        super().accept()

    def reject(self):
        super().reject()


