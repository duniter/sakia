'''
Created on 2 févr. 2014

@author: inso
'''
import logging
from math import pow

from PyQt5.QtWidgets import QDialog, QFrame, QSlider, QLabel, QDialogButtonBox, QErrorMessage
from PyQt5.QtCore import Qt, QSignalMapper


from cutecoin.models.coin import Coin
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
        for wallet in sender.wallets.wallets_list:
            self.combo_wallets.addItem(wallet.getText())

        for contact in sender.contacts:
            self.combo_contact.addItem(contact.name)

        self.refresh_transaction(sender.wallets.wallets_list[0])

    def remove_coins_from_transfer(self):
        selection = self.list_coins_sent.selectedIndexes()
        wallet_coins = self.list_wallet.model().coins
        sent_coins = self.list_coins_sent.model().coins
        new_wallet = sent_coins
        for selected in selection:
            coin = sent_coins[selected.row()]
            sent_coins.remove(coin)
            wallet_coins.append(coin)
        self.list_wallet.setModel(CoinsListModel(wallet_coins))
        self.list_coins_sent.setModel(CoinsListModel(new_wallet))

    def add_coins_to_transfer(self):
        selection = self.list_wallet.selectedIndexes()
        wallet_coins = self.list_wallet.model().coins
        sent_coins = self.list_coins_sent.model().coins
        new_wallet = wallet_coins
        for selected in selection:
            coin = wallet_coins[selected.row()]
            new_wallet.remove(coin)
            sent_coins.append(coin)
        self.list_wallet.setModel(CoinsListModel(new_wallet))
        self.list_coins_sent.setModel(CoinsListModel(sent_coins))

    def open_manage_wallet_coins(self):
        pass

    def accept(self):
        sent_coins = self.list_coins_sent.model().toList()
        recipient = None

        if self.radio_key_fingerprint.isChecked():
            recipient = Person("", self.edit_key_fingerprint.text(), "")
        else:
            recipient = self.sender.contacts[
                self.combo_contact.currentIndex()]

        if self.radio_node_address.isChecked():
            node = Node(
                self.edit_node_address.text(), int(
                    self.edit_port.text()))
        else:
            # TODO: Manage trusted nodes
            node = Node(
                self.edit_node_address.text(), int(
                    self.edit_port.text()))

        message = self.edit_message.text()
        # TODO: Transfer money, and validate the window if no error happened
        if self.sender.transfer_coins(node, recipient, sent_coins, message):
            self.close()
        else:
            QErrorMessage(self).showMessage("Cannot transfer coins.")

    def change_displayed_wallet(self, index):
        wallet = self.sender.wallets.wallets_list[index]
        self.refresh_transaction(wallet)

    def refresh_transaction(self, wallet):
        coins_sent_model = CoinsListModel([])
        self.list_coins_sent.setModel(coins_sent_model)
        wallet_coins_model = CoinsListModel(list(wallet.coins))
        self.list_wallet.setModel(wallet_coins_model)

    def recipient_mode_changed(self, fingerprint_toggled):
        self.edit_key_fingerprint.setEnabled(fingerprint_toggled)
        self.combo_contact.setEnabled(not fingerprint_toggled)

    def transfer_mode_changed(self, node_address_toggled):
        self.edit_node_address.setEnabled(node_address_toggled)
        self.combo_trusted_node.setEnabled(not node_address_toggled)
