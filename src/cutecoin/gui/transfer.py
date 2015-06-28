"""
Created on 2 févr. 2014

@author: inso
"""
from PyQt5.QtWidgets import QDialog, QMessageBox, QApplication
from PyQt5.QtCore import QRegExp, Qt, QLocale, pyqtSlot
from PyQt5.QtGui import QRegExpValidator

from ..gen_resources.transfer_uic import Ui_TransferMoneyDialog
from . import toast
import asyncio


class TransferMoneyDialog(QDialog, Ui_TransferMoneyDialog):

    """
    classdocs
    """

    def __init__(self, sender, password_asker):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.account = sender
        self.password_asker = password_asker
        self.recipient_trusts = []
        self.wallet = None
        self.community = self.account.communities[0]
        self.wallet = self.account.wallets[0]
        self.dividend = self.community.dividend()

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

    def accept(self):
        comment = self.edit_message.text()

        if self.radio_contact.isChecked():
            index = self.combo_contact.currentIndex()
            recipient = self.account.contacts[index]['pubkey']
        else:
            recipient = self.edit_pubkey.text()
        amount = self.spinbox_amount.value()

        if not amount:
            QMessageBox.critical(self, self.tr("Money transfer"),
                                 self.tr("No amount. Please give the transfert amount"),
                                 QMessageBox.Ok)
            return

        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        self.wallet.transfer_broadcasted.connect(self.money_sent)
        self.wallet.broadcast_error.connect(self.handle_error)
        asyncio.async(self.wallet.send_money(self.account.salt, password, self.community,
                                   recipient, amount, comment))

    @pyqtSlot(str)
    def money_sent(self, receiver_uid):
        toast.display(self.tr("Transfer"),
                      self.tr("Success sending money to {0}").format(receiver_uid))
        self.wallet.transfer_broadcasted.disconnect()
        self.wallet.broadcast_error.disconnect(self.handle_error)
        QApplication.restoreOverrideCursor()
        super().accept()

    @pyqtSlot(int, str)
    def handle_error(self, error_code, text):
        toast.display(self.tr("Error"), self.tr("{0} : {1}".format(error_code, text)))
        self.wallet.transfer_broadcasted.disconnect()
        self.wallet.broadcast_error.disconnect(self.handle_error)
        QApplication.restoreOverrideCursor()

    def amount_changed(self):
        amount = self.spinbox_amount.value()
        relative = amount / self.dividend
        self.spinbox_relative.blockSignals(True)
        self.spinbox_relative.setValue(relative)
        self.spinbox_relative.blockSignals(False)

    def relative_amount_changed(self):
        relative = self.spinbox_relative.value()
        amount = relative * self.dividend
        self.spinbox_amount.blockSignals(True)
        self.spinbox_amount.setValue(amount)
        self.spinbox_amount.blockSignals(False)

    def change_current_community(self, index):
        self.community = self.account.communities[index]
        self.dividend = self.community.dividend()
        amount = self.wallet.value(self.community)
        ref_amount = self.account.units_to_ref(amount, self.community)
        ref_name = self.account.ref_name(self.community.currency)
        # if referential type is quantitative...
        if self.account.ref_type() == 'q':
            # display int values
            ref_amount = QLocale().toString(float(ref_amount), 'f', 0)
        else:
            # display float values
            ref_amount = QLocale().toString(ref_amount, 'f', 6)
        self.label_total.setText("{0} {1}".format(ref_amount, ref_name))
        self.spinbox_amount.setSuffix(" " + self.community.currency)
        self.spinbox_amount.setValue(0)
        amount = self.wallet.value(self.community)
        relative = amount / self.dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def change_displayed_wallet(self, index):
        self.wallet = self.account.wallets[index]
        amount = self.wallet.value(self.community)
        ref_amount = self.account.units_to_ref(amount, self.community)
        ref_name = self.account.ref_name(self.community.currency)
        # if referential type is quantitative...
        if self.account.ref_type() == 'q':
            # display int values
            ref_amount = QLocale().toString(float(ref_amount), 'f', 0)
        else:
            # display float values
            ref_amount = QLocale().toString(ref_amount, 'f', 6)
        self.label_total.setText("{0} {1}".format(ref_amount, ref_name))
        self.spinbox_amount.setValue(0)
        amount = self.wallet.value(self.community)
        relative = amount / self.dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)
