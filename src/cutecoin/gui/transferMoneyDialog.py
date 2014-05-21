'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QDialog, QErrorMessage


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
        self.wallet = sender.wallets[0]
        for wallet in sender.wallets:
            self.combo_wallets.addItem(wallet.get_text())

        for trust in wallet.trusts():
            self.combo_trusted_node.addItem(trust.get_text())

        for contact in sender.contacts:
            self.combo_contact.addItem(contact.name)

        self.refresh_transaction()

    def remove_coins_from_transfer(self):
        selection = self.list_coins_sent.selectedIndexes()
        wallet_coins = self.list_wallet.model().coins
        sent_coins = self.list_coins_sent.model().coins
        new_wallet = sent_coins
        for selected in selection:
            coin = sent_coins[selected.row()]
            sent_coins.remove(coin)
            wallet_coins.append(coin)
        self.list_wallet.setModel(CoinsListModel(self.wallet, wallet_coins))
        self.list_coins_sent.setModel(CoinsListModel(self.wallet, new_wallet))

    def add_coins_to_transfer(self):
        selection = self.list_wallet.selectedIndexes()
        wallet_coins = self.list_wallet.model().coins
        sent_coins = self.list_coins_sent.model().coins
        new_wallet_coins = wallet_coins
        for selected in selection:
            coin = wallet_coins[selected.row()]
            new_wallet_coins.remove(coin)
            sent_coins.append(coin)
        self.list_wallet.setModel(CoinsListModel(self.wallet,
                                                 new_wallet_coins))
        self.list_coins_sent.setModel(CoinsListModel(self.wallet, sent_coins))

    def open_manage_wallet_coins(self):
        pass

    def accept(self):
        sent_coins = self.list_coins_sent.model().to_list()
        recipient = None

        if self.radio_key_fingerprint.isChecked():
            recipient = Person("", self.edit_key_fingerprint.text(), "")
        else:
            recipient = self.sender.contacts[
                self.combo_contact.currentIndex()]

        if self.radio_node_address.isChecked():
            node = Node.create(
                self.edit_node_address.text(), int(
                    self.spinbox_port.text()))
        else:
            # TODO: Manage trusted nodes
            node = self.wallet.trusts()[self.combo_trusted_node.currentIndex()]

        message = self.edit_message.text()
        # TODO: Transfer money, and validate the window if no error happened
        error = self.wallet.transfer_coins(node, recipient, sent_coins, message)
        if error:
            QErrorMessage(self).showMessage("Cannot transfer coins " + error)
        else:
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
