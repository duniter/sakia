'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QErrorMessage, QInputDialog, QLineEdit

from cutecoin.core.person import Person

from cutecoin.gen_resources.transferDialog_uic import Ui_TransferMoneyDialog


class TransferMoneyDialog(QDialog, Ui_TransferMoneyDialog):

    '''
    classdocs
    '''

    def __init__(self, sender):
        '''
        Constructor
        '''
        super(TransferMoneyDialog, self).__init__()
        self.setupUi(self)
        self.sender = sender
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

    def accept(self):
        message = self.edit_message.text()
        recipient = self.edit_key_fingerprint.text()
        amount = self.spinbox_amount.value()
        password = QInputDialog.getText(self, "Wallet password",
                                        "Please enter your password",
                                        QLineEdit.Password)
        if password[1] is True:
            password = password[0]
        else:
            return

        error = self.wallet.send_money(self.sender.salt, password, self.community,
                                       recipient, amount, message)

        self.accepted.emit()
        self.close()

    def amount_changed(self):
        amount = self.spinbox_amount.value()
        dividend = self.community.dividend()
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
        self.label_total.setText(self.wallet.get_text(self.community))
        self.spinbox_amount.setSuffix(" " + self.community.currency)
        self.spinbox_amount.setValue(0)
        self.spinbox_amount.setMaximum(self.wallet.value(self.community))

    def change_displayed_wallet(self, index):
        self.wallet = self.sender.wallets[index]
        self.label_total.setText(self.wallet.get_text(self.community))
        self.spinbox_amount.setValue(0)
        self.spinbox_amount.setMaximum(self.wallet.value(self.community))

    def recipient_mode_changed(self, fingerprint_toggled):
        self.edit_key_fingerprint.setEnabled(fingerprint_toggled)
        self.combo_contact.setEnabled(not fingerprint_toggled)
