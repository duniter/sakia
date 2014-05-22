'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QErrorMessage


import ucoin
from cutecoin.models.person import Person
from cutecoin.models.node import Node
from cutecoin.models.coin.listModel import CoinsListModel

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

        self.refresh_transaction()

    def remove_coins_from_transfer(self):
        selection = self.list_coins_sent.selectedIndexes()
        for select in selection:
            coins = self.list_coins_sent.model().remove_coins(select, 1)
            self.list_wallet.model().add_coins(coins)
        self.label_total.setText("Total : %d" %
                                 self.list_coins_sent.model().total())

    def add_coins_to_transfer(self):
        selection = self.list_wallet.selectedIndexes()
        for select in selection:
            coins = self.list_wallet.model().remove_coins(select, 1)
            self.list_coins_sent.model().add_coins(coins)
        self.label_total.setText("Total : %d"
                                 % self.list_coins_sent.model().total())

    def accept(self):
        sent_coins = self.list_coins_sent.model().to_list()
        recipient = None

        if self.radio_key_fingerprint.isChecked():
            recipient = Person("", self.edit_key_fingerprint.text(), "")
        else:
            recipient = self.sender.contacts[
                self.combo_contact.currentIndex()]

        message = self.edit_message.text()
        # TODO: All nodes trusted by recipient
        error = self.wallet.transfer_coins(recipient, sent_coins, message)
        if error:
            QErrorMessage(self).showMessage("Cannot transfer coins " + error)
        else:
            self.accepted.emit()
            self.close()

    def change_displayed_wallet(self, index):
        self.wallet = self.sender.wallets[index]
        self.refresh_transaction()

    def refresh_transaction(self):
        coins_sent_model = CoinsListModel(self.wallet, [])
        self.list_coins_sent.setModel(coins_sent_model)
        wallet_coins_model = CoinsListModel(self.wallet,
                                            list(self.wallet.coins))
        self.list_wallet.setModel(wallet_coins_model)

    def recipient_mode_changed(self, fingerprint_toggled):
        self.edit_key_fingerprint.setEnabled(fingerprint_toggled)
        self.combo_contact.setEnabled(not fingerprint_toggled)

    def transfer_mode_changed(self, node_address_toggled):
        self.edit_node_address.setEnabled(node_address_toggled)
        self.combo_trusted_node.setEnabled(not node_address_toggled)
