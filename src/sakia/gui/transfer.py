"""
Created on 2 févr. 2014

@author: inso
"""
import asyncio

from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import QRegExp, Qt

from PyQt5.QtGui import QRegExpValidator

from ..gen_resources.transfer_uic import Ui_TransferMoneyDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.dialogs import QAsyncMessageBox, QMessageBox
from ..tools.decorators import asyncify


class TransferMoneyDialog(QDialog, Ui_TransferMoneyDialog):

    """
    classdocs
    """

    def __init__(self, app, sender, password_asker, community, transfer):
        """
        Constructor
        :param sakia.core.Application app: The application
        :param sakia.core.Account sender: The sender
        :param sakia.gui.password_asker.Password_Asker password_asker: The password asker
        :return:
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = sender
        self.password_asker = password_asker
        self.recipient_trusts = []
        self.transfer = transfer
        self.wallet = None
        self.community = community if community else self.account.communities[0]
        self.wallet = self.account.wallets[0]

        regexp = QRegExp('^([ a-zA-Z0-9-_:/;*?\[\]\(\)\\\?!^+=@&~#{}|<>%.]{0,255})$')
        validator = QRegExpValidator(regexp)
        self.edit_message.setValidator(validator)

        for community in self.account.communities:
            self.combo_community.addItem(community.currency)

        for wallet in self.account.wallets:
            self.combo_wallets.addItem(wallet.name)

        for contact_name in sorted([c['name'] for c in sender.contacts], key=str.lower):
            self.combo_contact.addItem(contact_name)

        if len(self.account.contacts) == 0:
            self.combo_contact.setEnabled(False)
            self.radio_contact.setEnabled(False)
            self.radio_pubkey.setChecked(True)

        self.combo_community.setCurrentText(self.community.name)

        if self.transfer:
            sender = self.transfer.metadata['issuer']
            wallet_index = [w.pubkey for w in app.current_account.wallets].index(sender)
            self.combo_wallets.setCurrentIndex(wallet_index)
            self.edit_pubkey.setText(transfer.metadata['receiver'])
            self.radio_pubkey.setChecked(True)
            self.edit_message.setText(transfer.metadata['comment'])


    @classmethod
    async def send_money_to_identity(cls, app, account, password_asker, community, identity):
        dialog = cls(app, account, password_asker, community, None)
        dialog.edit_pubkey.setText(identity.pubkey)
        dialog.radio_pubkey.setChecked(True)
        return (await dialog.async_exec())

    @classmethod
    async def send_transfer_again(cls, app, account, password_asker, community, transfer):
        dialog = cls(app, account, password_asker, community, transfer)
        dividend = await community.dividend()
        relative = transfer.metadata['amount'] / dividend
        dialog.spinbox_amount.setMaximum(transfer.metadata['amount'])
        dialog.spinbox_relative.setMaximum(relative)
        dialog.spinbox_amount.setValue(transfer.metadata['amount'])

        return (await dialog.async_exec())

    @asyncify
    async def accept(self):
        self.button_box.setEnabled(False)
        comment = self.edit_message.text()

        if self.radio_contact.isChecked():
            for contact in self.account.contacts:
                if contact['name'] == self.combo_contact.currentText():
                    recipient = contact['pubkey']
                    break
        else:
            recipient = self.edit_pubkey.text()
        amount = self.spinbox_amount.value()

        if not amount:
            await QAsyncMessageBox.critical(self, self.tr("Money transfer"),
                                 self.tr("No amount. Please give the transfert amount"),
                                 QMessageBox.Ok)
            self.button_box.setEnabled(True)
            return

        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        result = await self.wallet.send_money(self.account.salt, password, self.community,
                                   recipient, amount, comment)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            else:
                await QAsyncMessageBox.information(self, self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            QApplication.restoreOverrideCursor()

            # If we sent back a transaction we cancel the first one
            if self.transfer:
                self.transfer.cancel()

            super().accept()
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"), "Error : {0}".format(result[1]))
            else:
                await QAsyncMessageBox.critical(self, self.tr("Transfer"), result[1])

            QApplication.restoreOverrideCursor()
            self.button_box.setEnabled(True)

    @asyncify
    async def amount_changed(self, value):
        dividend = await self.community.dividend()
        relative = value / dividend
        self.spinbox_relative.blockSignals(True)
        self.spinbox_relative.setValue(relative)
        self.spinbox_relative.blockSignals(False)

    @asyncify
    async def relative_amount_changed(self, value):
        dividend = await self.community.dividend()
        amount = value * dividend
        self.spinbox_amount.blockSignals(True)
        self.spinbox_amount.setValue(amount)
        self.spinbox_amount.blockSignals(False)

    @asyncify
    async def change_current_community(self, index):
        self.community = self.account.communities[index]
        amount = await self.wallet.value(self.community)

        ref_text = await self.account.current_ref(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.label_total.setText("{0}".format(ref_text))
        self.spinbox_amount.setSuffix(" " + self.community.currency)
        amount = await self.wallet.value(self.community)
        dividend = await self.community.dividend()
        relative = amount / dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    @asyncify
    async def change_displayed_wallet(self, index):
        self.wallet = self.account.wallets[index]
        amount = await self.wallet.value(self.community)
        ref_text = await self.account.current_ref(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.label_total.setText("{0}".format(ref_text))
        amount = await self.wallet.value(self.community)
        dividend = await self.community.dividend()
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
