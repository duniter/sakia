"""
Created on 2 févr. 2014

@author: inso
"""
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication
from PyQt5.QtCore import QRegExp, Qt, QLocale, pyqtSlot
from PyQt5.QtGui import QRegExpValidator

from ..gen_resources.transfer_uic import Ui_TransferMoneyDialog
from . import toast
from ..tools.decorators import asyncify
import asyncio


class TransferMoneyDialog(QDialog, Ui_TransferMoneyDialog):

    """
    classdocs
    """

    def __init__(self, app, sender, password_asker):
        """
        Constructor
        :param cutecoin.core.Application app: The application
        :param cutecoin.core.Account sender: The sender
        :param cutecoin.gui.password_asker.Password_Asker password_asker: The password asker
        :return:
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = sender
        self.password_asker = password_asker
        self.recipient_trusts = []
        self.wallet = None
        self.community = self.account.communities[0]
        self.wallet = self.account.wallets[0]

        regexp = QRegExp('^([ a-zA-Z0-9-_:/;*?\[\]\(\)\\\?!^+=@&~#{}|<>%.]{0,255})$')
        validator = QRegExpValidator(regexp)
        self.edit_message.setValidator(validator)

        for community in self.account.communities:
            self.combo_community.addItem(community.currency)

        for wallet in self.account.wallets:
            self.combo_wallets.addItem(wallet.name)

        for contact in sender.contacts:
            self.combo_contact.addItem(contact['name'])

        if len(self.account.contacts) == 0:
            self.combo_contact.setEnabled(False)
            self.radio_contact.setEnabled(False)
            self.radio_pubkey.setChecked(True)

    @classmethod
    @asyncify
    @asyncio.coroutine
    def send_money_to_identity(cls, app, account, password_asker, community, identity):
        dialog = cls(app, account, password_asker)
        dialog.edit_pubkey.setText(identity.pubkey)
        dialog.combo_community.setCurrentText(community.name)
        dialog.radio_pubkey.setChecked(True)
        yield from dialog.async_exec()

    @asyncify
    @asyncio.coroutine
    def accept(self):
        comment = self.edit_message.text()

        if self.radio_contact.isChecked():
            index = self.combo_contact.currentIndex()
            recipient = self.account.contacts[index]['pubkey']
        else:
            recipient = self.edit_pubkey.text()
        amount = self.spinbox_amount.value()

        if not amount:
            return
            """
            QMessageBox.critical(self, self.tr("Money transfer"),
                                 self.tr("No amount. Please give the transfert amount"),
                                 QMessageBox.Ok)
            return"""

        password = yield from self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        result = yield from self.wallet.send_money(self.account.salt, password, self.community,
                                   recipient, amount, comment)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            QApplication.restoreOverrideCursor()
            super().accept()
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Error"), "{0}".format(result[1]))
            QApplication.restoreOverrideCursor()

    @asyncify
    @asyncio.coroutine
    def amount_changed(self, value):
        dividend = yield from self.community.dividend()
        relative = value / dividend
        self.spinbox_relative.blockSignals(True)
        self.spinbox_relative.setValue(relative)
        self.spinbox_relative.blockSignals(False)

    @asyncify
    @asyncio.coroutine
    def relative_amount_changed(self, value):
        dividend = yield from self.community.dividend()
        amount = value * dividend
        self.spinbox_amount.blockSignals(True)
        self.spinbox_amount.setValue(amount)
        self.spinbox_amount.blockSignals(False)

    @asyncify
    @asyncio.coroutine
    def change_current_community(self, index):
        self.community = self.account.communities[index]
        amount = yield from self.wallet.value(self.community)

        ref_text = yield from self.account.current_ref(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.label_total.setText("{0}".format(ref_text))
        self.spinbox_amount.setSuffix(" " + self.community.currency)
        self.spinbox_amount.setValue(0)
        amount = yield from self.wallet.value(self.community)
        dividend = yield from self.community.dividend()
        relative = amount / dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    @asyncify
    @asyncio.coroutine
    def change_displayed_wallet(self, index):
        self.wallet = self.account.wallets[index]
        amount = yield from self.wallet.value(self.community)
        ref_text = yield from self.account.current_ref(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.label_total.setText("{0}".format(ref_text))
        self.spinbox_amount.setValue(0)
        amount = yield from self.wallet.value(self.community)
        dividend = yield from self.community.dividend()
        relative = amount / dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)

    def async_exec(self):
        future = asyncio.Future()
        self.finished.connect(lambda r: future.set_result(r))
        self.open()
        return future
