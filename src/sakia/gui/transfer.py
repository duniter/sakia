"""
Created on 2 févr. 2014

@author: inso
"""
import asyncio

from PyQt5.QtWidgets import QDialog, QApplication
from PyQt5.QtCore import QRegExp, Qt, QObject

from PyQt5.QtGui import QRegExpValidator

from ..gen_resources.transfer_uic import Ui_TransferMoneyDialog
from .widgets import toast
from .widgets.dialogs import QAsyncMessageBox, QMessageBox
from ..tools.decorators import asyncify


class TransferMoneyDialog(QObject):

    """
    classdocs
    """

    def __init__(self, app, account, password_asker, community, transfer, widget=QDialog, view=Ui_TransferMoneyDialog):
        """
        Constructor
        :param sakia.core.Application app: The application
        :param sakia.core.Account account: The account
        :param sakia.gui.password_asker.Password_Asker password_asker: The password asker
        :param sakia.core.Community community:
        :param sakia.core.Transfer transfer:
        :param class widget:
        :param class view:
        :return:
        """
        super().__init__()
        self.widget = widget()
        self.ui = view()
        self.ui.setupUi(self.widget)

        self.app = app
        self.account = account
        self.password_asker = password_asker
        self.recipient_trusts = []
        self.transfer = transfer
        self.wallet = None
        self.community = community if community else self.account.communities[0]
        self.wallet = self.account.wallets[0]

        self.ui.radio_contact.toggled.connect(lambda c, radio="contact": self.recipient_mode_changed(radio))
        self.ui.radio_pubkey.toggled.connect(lambda c, radio="pubkey": self.recipient_mode_changed(radio))
        self.ui.radio_search.toggled.connect(lambda c, radio="search": self.recipient_mode_changed(radio))
        self.ui.button_box.accepted.connect(self.accept)
        self.ui.button_box.rejected.connect(self.widget.reject)
        self.ui.combo_wallets.currentIndexChanged.connect(self.change_displayed_wallet)
        self.ui.combo_community.currentIndexChanged.connect(self.change_current_community)
        self.ui.spinbox_relative.valueChanged.connect(self.relative_amount_changed)
        self.ui.spinbox_amount.valueChanged.connect(self.amount_changed)
        self.ui.search_user.button_reset.hide()
        self.ui.search_user.init(self.app)
        self.ui.search_user.change_account(self.account)
        self.ui.search_user.change_community(self.community)

        regexp = QRegExp('^([ a-zA-Z0-9-_:/;*?\[\]\(\)\\\?!^+=@&~#{}|<>%.]{0,255})$')
        validator = QRegExpValidator(regexp)
        self.ui.edit_message.setValidator(validator)

        for community in self.account.communities:
            self.ui.combo_community.addItem(community.currency)

        for wallet in self.account.wallets:
            self.ui.combo_wallets.addItem(wallet.name)

        for contact_name in sorted([c['name'] for c in account.contacts], key=str.lower):
            self.ui.combo_contact.addItem(contact_name)

        if len(self.account.contacts) == 0:
            self.ui.combo_contact.setEnabled(False)
            self.ui.radio_contact.setEnabled(False)
            self.ui.radio_pubkey.setChecked(True)

        self.ui.combo_community.setCurrentText(self.community.name)

        if self.transfer:
            account = self.transfer.metadata['issuer']
            wallet_index = [w.pubkey for w in app.current_account.wallets].index(account)
            self.ui.combo_wallets.setCurrentIndex(wallet_index)
            self.ui.edit_pubkey.setText(transfer.metadata['receiver'])
            self.ui.radio_pubkey.setChecked(True)
            self.ui.edit_message.setText(transfer.metadata['comment'])

    @classmethod
    async def send_money_to_identity(cls, app, account, password_asker, community, identity):
        dialog = cls(app, account, password_asker, community, None)
        dialog.ui.edit_pubkey.setText(identity.pubkey)
        dialog.ui.radio_pubkey.setChecked(True)
        return await dialog.async_exec()

    @classmethod
    async def send_transfer_again(cls, app, account, password_asker, community, transfer):
        dialog = cls(app, account, password_asker, community, transfer)
        dividend = await community.dividend()
        relative = transfer.metadata['amount'] / dividend
        dialog.ui.spinbox_amount.setMaximum(transfer.metadata['amount'])
        dialog.ui.spinbox_relative.setMaximum(relative)
        dialog.ui.spinbox_amount.setValue(transfer.metadata['amount'])

        return await dialog.async_exec()

    @asyncify
    async def accept(self):
        self.ui.button_box.setEnabled(False)
        comment = self.ui.edit_message.text()

        if self.ui.radio_contact.isChecked():
            for contact in self.account.contacts:
                if contact['name'] == self.ui.combo_contact.currentText():
                    recipient = contact['pubkey']
                    break
        elif self.ui.radio_search.isChecked():
            if self.ui.search_user.current_identity():
                recipient = self.ui.search_user.current_identity().pubkey
            else:
                return
        else:
            recipient = self.ui.edit_pubkey.text()
        amount = self.ui.spinbox_amount.value()

        if not amount:
            await QAsyncMessageBox.critical(self.widget, self.tr("Money transfer"),
                                 self.tr("No amount. Please give the transfert amount"),
                                 QMessageBox.Ok)
            self.ui.button_box.setEnabled(True)
            return

        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)

        result = await self.wallet.send_money(self.account.salt, password, self.community,
                                   recipient, amount, comment)
        if result[0]:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            else:
                await QAsyncMessageBox.information(self.widget, self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            QApplication.restoreOverrideCursor()

            # If we sent back a transaction we cancel the first one
            if self.transfer:
                self.transfer.cancel()
            self.app.refresh_transfers.emit()
            self.widget.accept()
        else:
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"), "Error : {0}".format(result[1]))
            else:
                await QAsyncMessageBox.critical(self.widget, self.tr("Transfer"), result[1])

            QApplication.restoreOverrideCursor()
            self.ui.button_box.setEnabled(True)

    @asyncify
    async def amount_changed(self, value):
        dividend = await self.community.dividend()
        relative = value / dividend
        self.ui.spinbox_relative.blockSignals(True)
        self.ui.spinbox_relative.setValue(relative)
        self.ui.spinbox_relative.blockSignals(False)

    @asyncify
    async def relative_amount_changed(self, value):
        dividend = await self.community.dividend()
        amount = value * dividend
        self.ui.spinbox_amount.blockSignals(True)
        self.ui.spinbox_amount.setValue(amount)
        self.ui.spinbox_amount.blockSignals(False)

    @asyncify
    async def change_current_community(self, index):
        self.community = self.account.communities[index]
        amount = await self.wallet.value(self.community)

        ref_text = await self.account.current_ref.instance(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.ui.label_total.setText("{0}".format(ref_text))
        self.ui.spinbox_amount.setSuffix(" " + self.community.currency)
        amount = await self.wallet.value(self.community)
        dividend = await self.community.dividend()
        relative = amount / dividend
        self.ui.spinbox_amount.setMaximum(amount)
        self.ui.spinbox_relative.setMaximum(relative)

    @asyncify
    async def change_displayed_wallet(self, index):
        self.wallet = self.account.wallets[index]
        amount = await self.wallet.value(self.community)
        ref_text = await self.account.current_ref.instance(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.ui.label_total.setText("{0}".format(ref_text))
        amount = await self.wallet.value(self.community)
        dividend = await self.community.dividend()
        relative = amount / dividend
        self.ui.spinbox_amount.setMaximum(amount)
        self.ui.spinbox_relative.setMaximum(relative)

    def recipient_mode_changed(self, radio):
        self.ui.edit_pubkey.setEnabled(radio == "pubkey")
        self.ui.combo_contact.setEnabled(radio == "contact")
        self.ui.search_user.setEnabled(radio == "search")

    def async_exec(self):
        future = asyncio.Future()
        self.widget.finished.connect(lambda r: future.set_result(r))
        self.widget.open()
        return future

    def exec(self):
        self.widget.exec()