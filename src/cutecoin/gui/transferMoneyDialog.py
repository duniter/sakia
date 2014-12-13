'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QErrorMessage


from cutecoin.models.person import Person
from cutecoin.models.node import Node

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
        self.wallet = sender.wallets[0]
        for wallet in sender.wallets:
            self.combo_wallets.addItem(wallet.get_text())

        for contact in sender.contacts:
            self.combo_contact.addItem(contact.name)

    def refresh_total(self):
        dividend = self.wallet.get_block()['dividend']
        total = self.list_coins_sent.model().total()
        relative_total = total / int(dividend)
        self.label_total.setText("Total : \n \
%d %s \n \
%.2f UD" % (total, self.wallet.currency, relative_total))

    def accept(self):
        message = self.edit_message.text()
        #error = self.wallet.send_money(recipient, amount, message)

        self.accepted.emit()
        self.close()

    def change_displayed_wallet(self, index):
        self.wallet = self.sender.wallets[index]
        self.refresh_transaction()

    def recipient_mode_changed(self, fingerprint_toggled):
        self.edit_key_fingerprint.setEnabled(fingerprint_toggled)
        self.combo_contact.setEnabled(not fingerprint_toggled)
