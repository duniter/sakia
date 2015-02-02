'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QMessageBox

from ..tools.exceptions import NotEnoughMoneyError, NoPeerAvailable
from ..gen_resources.transfer_uic import Ui_TransferMoneyDialog

import logging


class TransferMoneyDialog(QDialog, Ui_TransferMoneyDialog):

    '''
    classdocs
    '''

    def __init__(self, sender, password_asker):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.sender = sender
        self.password_asker = password_asker
        self.recipient_trusts = []
        self.wallet = None
        self.community = self.sender.communities[0]
        self.wallet = self.sender.wallets[0]
        self.dividend = self.community.dividend()

        for community in self.sender.communities:
            self.combo_community.addItem(community.currency)

        for wallet in self.sender.wallets:
            self.combo_wallets.addItem(wallet.name)

        for contact in sender.contacts:
            self.combo_contact.addItem(contact.name)

        if len(self.sender.contacts) == 0:
            self.combo_contact.setEnabled(False)
            self.radio_contact.setEnabled(False)
            self.radio_pubkey.setChecked(True)

    def accept(self):
        comment = self.edit_message.text()

        if self.radio_contact.isChecked():
            index = self.combo_contact.currentIndex()
            recipient = self.sender.contacts[index].pubkey
        else:
            recipient = self.edit_pubkey.text()
        amount = self.spinbox_amount.value()

        password = self.password_asker.exec_()
        if self.password_asker.result() == QDialog.Rejected:
            return

        try:
            self.wallet.send_money(self.sender.salt, password, self.community,
                                       recipient, amount, comment)
            QMessageBox.information(self, "Money transfer",
                                 "Success transfering {0} {1} to {2}".format(amount,
                                                                             self.community.currency,
                                                                             recipient))
        except ValueError as e:
            QMessageBox.critical(self, "Money transfer",
                                 "Something wrong happened : {0}".format(e),
                                 QMessageBox.Ok)
            return
        except NotEnoughMoneyError as e:
            QMessageBox.critical(self, "Money transfer",
                                 "You don't have enough money available in this block : \n{0}"
                                 .format(e.message))
            return
        except NoPeerAvailable as e:
            QMessageBox.critical(self, "Money transfer",
                                 "Couldn't connect to network : {0}".format(e),
                                 QMessageBox.Ok)
            return
        except Exception as e:
            QMessageBox.critical(self, "Error",
                                 "{0}".format(e),
                                 QMessageBox.Ok)
            return
        super().accept()

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
        self.community = self.sender.communities[index]
        self.dividend = self.community.dividend()
        amount = self.wallet.value(self.community)
        ref_amount = self.sender.units_to_ref(amount, self.community)
        ref_name = self.sender.ref_name(self.community.currency)
        self.label_total.setText("{0} {1}".format(ref_amount, ref_name))
        self.spinbox_amount.setSuffix(" " + self.community.currency)
        self.spinbox_amount.setValue(0)
        amount = self.wallet.value(self.community)
        relative = amount / self.dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def change_displayed_wallet(self, index):
        self.wallet = self.sender.wallets[index]
        amount = self.wallet.value(self.community)
        ref_amount = self.sender.units_to_ref(amount, self.community)
        ref_name = self.sender.ref_name(self.community.currency)
        self.label_total.setText("{0} {1}".format(ref_amount, ref_name))
        self.spinbox_amount.setValue(0)
        amount = self.wallet.value(self.community)
        relative = amount / self.dividend
        self.spinbox_amount.setMaximum(amount)
        self.spinbox_relative.setMaximum(relative)

    def recipient_mode_changed(self, pubkey_toggled):
        self.edit_pubkey.setEnabled(pubkey_toggled)
        self.combo_contact.setEnabled(not pubkey_toggled)
