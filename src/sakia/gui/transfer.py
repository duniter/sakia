"""
Created on 2 févr. 2014

@author: inso
"""
import asyncio
import logging

from PyQt5.QtWidgets import QDialog, QApplication, QDialogButtonBox
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
        self.ui.search_user.search_started.connect(lambda: self.ui.button_box.setEnabled(False))
        self.ui.search_user.search_completed.connect(lambda: self.ui.button_box.setEnabled(True))

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
        logging.debug("Accept transfer action...")
        self.ui.button_box.setEnabled(False)
        comment = self.ui.edit_message.text()

        logging.debug("checking recipient mode...")
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

        logging.debug("checking amount...")
        if not amount:
            await QAsyncMessageBox.critical(self.widget, self.tr("Money transfer"),
                                 self.tr("No amount. Please give the transfert amount"),
                                 QMessageBox.Ok)
            self.ui.button_box.setEnabled(True)
            return
        logging.debug("Showing password dialog...")
        password = await self.password_asker.async_exec()
        if self.password_asker.result() == QDialog.Rejected:
            self.ui.button_box.setEnabled(True)
            return

        logging.debug("Setting cursor...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        logging.debug("Send money...")
        result = await self.wallet.send_money(self.account.salt, password, self.community,
                                   recipient, amount, comment)
        if result[0]:
            logging.debug("Checking result to display...")
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            else:
                await QAsyncMessageBox.information(self.widget, self.tr("Transfer"),
                          self.tr("Success sending money to {0}").format(recipient))
            logging.debug("Restore cursor...")
            QApplication.restoreOverrideCursor()

            # If we sent back a transaction we cancel the first one
            if self.transfer:
                self.transfer.cancel()
            self.app.refresh_transfers.emit()
            self.widget.accept()
        else:
            logging.debug("Error occured...")
            if self.app.preferences['notifications']:
                toast.display(self.tr("Transfer"), "Error : {0}".format(result[1]))
            else:
                await QAsyncMessageBox.critical(self.widget, self.tr("Transfer"), result[1])

            QApplication.restoreOverrideCursor()
            self.ui.button_box.setEnabled(True)

    @asyncify
    async def amount_changed(self, value):
        ud_block = await self.community.get_ud_block()
        if ud_block:
            dividend = ud_block['dividend']
            base = ud_block['unitbase']
        else:
            dividend = 1
            base = 0
        relative = value / (dividend * pow(10, base))
        self.ui.spinbox_relative.blockSignals(True)
        self.ui.spinbox_relative.setValue(relative)
        self.ui.spinbox_relative.blockSignals(False)
        correct_amount = int(pow(10, base) * round(float(value) / pow(10, base)))
        self.ui.button_box.button(QDialogButtonBox.Ok).setEnabled(correct_amount == value)

    @asyncify
    async def relative_amount_changed(self, value):
        ud_block = await self.community.get_ud_block()
        if ud_block:
            dividend = ud_block['dividend']
            base = ud_block['unitbase']
        else:
            dividend = 1
            base = 0
        amount = value * dividend * pow(10, base)
        amount = int(pow(10, base) * round(float(amount) / pow(10, base)))
        self.ui.spinbox_amount.blockSignals(True)
        self.ui.spinbox_amount.setValue(amount)
        self.ui.spinbox_amount.blockSignals(False)
        self.ui.button_box.button(QDialogButtonBox.Ok).setEnabled(True)

    @asyncify
    async def change_current_community(self, index):
        self.community = self.account.communities[index]
        amount = await self.wallet.value(self.community)

        ref_text = await self.account.current_ref.instance(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.ui.label_total.setText("{0}".format(ref_text))
        self.ui.spinbox_amount.setSuffix(" " + self.community.currency)
        await self.refresh_spinboxes()

    @asyncify
    async def change_displayed_wallet(self, index):
        self.wallet = self.account.wallets[index]
        amount = await self.wallet.value(self.community)
        ref_text = await self.account.current_ref.instance(amount, self.community, self.app)\
            .diff_localized(units=True,
                            international_system=self.app.preferences['international_system_of_units'])
        self.ui.label_total.setText("{0}".format(ref_text))
        await self.refresh_spinboxes()

    async def refresh_spinboxes(self):
        max_amount = await self.wallet.value(self.community)
        ud_block = await self.community.get_ud_block()
        if ud_block:
            dividend = ud_block['dividend']
            base = ud_block['unitbase']
        else:
            dividend = 1
            base = 0
        max_amount = int(pow(10, base) * round(float(max_amount) / pow(10, base)))
        max_relative = max_amount / dividend
        self.ui.spinbox_amount.setMaximum(max_amount)
        self.ui.spinbox_relative.setMaximum(max_relative)
        self.ui.spinbox_amount.setSingleStep(pow(10, base))

    def recipient_mode_changed(self, radio):
        self.ui.edit_pubkey.setEnabled(radio == "pubkey")
        self.ui.combo_contact.setEnabled(radio == "contact")
        self.ui.search_user.setEnabled(radio == "search")

    def async_exec(self):
        future = asyncio.Future()
        self.widget.finished.connect(lambda r: future.set_result(r) and self.widget.finished.disconnect())
        self.widget.open()
        return future

    def exec(self):
        self.widget.exec()