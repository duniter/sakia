'''
Created on 2 févr. 2014

@author: inso
'''

import logging
import time

from ucoinpy.api import bma
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from PyQt5.QtCore import QModelIndex, Qt, pyqtSlot, QObject, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from ..gen_resources.currency_tab_uic import Ui_CurrencyTabWidget
from .community_tab import CommunityTabWidget
from ..models.sent import SentListModel
from ..models.received import ReceivedListModel
from ..models.wallets import WalletsListModel
from ..models.wallet import WalletListModel


class BlockchainWatcher(QObject):
    def __init__(self, account, community):
        super().__init__()
        self.account = account
        self.community = community
        self.exiting = False
        self.last_block = self.community.request(bma.blockchain.Current)['number']

    @pyqtSlot()
    def watch(self):
        while not self.exiting:
            time.sleep(10)
            current_block = self.community.request(bma.blockchain.Current)
            if self.last_block != current_block['number']:
                for w in self.account.wallets:
                    w.cache.refresh(self.community)

                logging.debug("New block, {0} mined in {1}".format(self.last_block,
                                                                   self.community.currency))
                self.new_block_mined.emit(current_block['number'])
                self.last_block = current_block['number']

    new_block_mined = pyqtSignal(int)


class CurrencyTabWidget(QWidget, Ui_CurrencyTabWidget):

    '''
    classdocs
    '''

    def __init__(self, app, community, password_asker, status_label):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community
        self.password_asker = password_asker
        self.status_label = status_label
        self.tab_community = CommunityTabWidget(self.app.current_account,
                                                    self.community,
                                                    self.password_asker)
        self.bc_watcher = BlockchainWatcher(self.app.current_account,
                                                community)
        self.bc_watcher.new_block_mined.connect(self.refresh_block)

        self.watcher_thread = QThread()
        self.bc_watcher.moveToThread(self.watcher_thread)
        self.watcher_thread.started.connect(self.bc_watcher.watch)

        self.watcher_thread.start()

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
            self.tab_community = CommunityTabWidget(self.app.current_account,
                                                    self.community,
                                                    self.password_asker)
            self.tabs_account.addTab(self.tab_community,
                                     QIcon(':/icons/community_icon'),
                                    "Community")
            block_number = self.community.request(bma.blockchain.Current)['number']
            self.status_label.setText("Connected : Block {0}"
                                             .format(block_number))

    @pyqtSlot(int)
    def refresh_block(self, block_number):
        if self.list_wallet_content.model():
            self.list_wallet_content.model().dataChanged.emit(
                                                 QModelIndex(),
                                                 QModelIndex(),
                                                 [])
        if self.list_wallet_content.model():
            self.list_transactions_sent.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])

        if self.list_transactions_received.model():
            self.list_transactions_received.model().dataChanged.emit(
                                                         QModelIndex(),
                                                         QModelIndex(),
                                                         [])

        if self.tab_community.list_community_members.model():
            self.tab_community.list_community_members.model().dataChanged.emit(
                                                           QModelIndex(),
                                                           QModelIndex(),
                                                           [])

        self.label_current_block.setText("Connected : Block {0}"
                                             .format(block_number))

    def refresh_wallets(self):
        wallets_list_model = WalletsListModel(self.app.current_account,
                                              self.community)
        wallets_list_model.dataChanged.connect(self.wallet_changed)
        self.list_wallets.setModel(wallets_list_model)
        self.refresh_wallet_content(QModelIndex())

    def refresh_wallet_content(self, index):
        current_wallet = self.app.current_account.wallets[index.row()]
        wallet_list_model = WalletListModel(current_wallet, self.community)
        self.list_wallet_content.setModel(wallet_list_model)

    def wallet_context_menu(self, point):
        index = self.list_wallets.indexAt(point)
        model = self.list_wallets.model()
        if index.row() < model.rowCount(None):
            wallet = model.wallets[index.row()]
            menu = QMenu(model.data(index, Qt.DisplayRole), self)

            rename = QAction("Rename", self)
            rename.triggered.connect(self.rename_wallet)
            rename.setData(index)

            copy_pubkey = QAction("Copy pubkey to clipboard", self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(wallet)

            menu.addAction(rename)
            menu.addAction(copy_pubkey)
            # Show the context menu.
            menu.exec_(self.list_wallets.mapToGlobal(point))

    def rename_wallet(self):
        index = self.sender().data()
        self.list_wallets.edit(index)

    def copy_pubkey_to_clipboard(self):
        wallet = self.sender().data()
        clipboard = QApplication.clipboard()
        clipboard.setText(wallet.pubkey)

    def wallet_changed(self):
        self.app.save(self.app.current_account)

    def showEvent(self, event):
        block_number = self.community.request(bma.blockchain.Current)['number']
        self.status_label.setText("Connected : Block {0}"
                                         .format(block_number))

    def closeEvent(self, event):
        self.bc_watcher.deleteLater()
        self.watcher_thread.deleteLater()
