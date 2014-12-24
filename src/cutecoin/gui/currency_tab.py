'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget, QErrorMessage
from PyQt5.QtCore import QModelIndex
from cutecoin.gen_resources.currency_tab_uic import Ui_CurrencyTabWidget
from cutecoin.gui.community_tab import CommunityTabWidget
from cutecoin.models.sent import SentListModel
from cutecoin.models.received import ReceivedListModel
from cutecoin.models.wallets import WalletsListModel
from ..models.wallet import WalletListModel


class CurrencyTabWidget(QWidget, Ui_CurrencyTabWidget):

    '''
    classdocs
    '''

    def __init__(self, app, community):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community

    def refresh(self):
        if self.app.current_account is None:
            self.tabs_account.setEnabled(False)
        else:
            self.tabs_account.setEnabled(True)
            self.refresh_wallets()

            self.list_transactions_sent.setModel(
                SentListModel(self.app.current_account, self.community))
            self.list_transactions_received.setModel(
                ReceivedListModel(self.app.current_account, self.community))
            tab_community = CommunityTabWidget(self.app.current_account,
                                                    self.community)
            self.tabs_account.addTab(tab_community, "Community")

    def refresh_wallets(self):
        wallets_list_model = WalletsListModel(self.app.current_account)
        self.list_wallets.setModel(wallets_list_model)
        self.refresh_wallet_content(QModelIndex())

    def refresh_wallet_content(self, index):
        current_wallet = self.app.current_account.wallets[index.row()]
        wallet_list_model = WalletListModel(current_wallet, self.community)
        self.list_wallet_content.setModel(wallet_list_model)
