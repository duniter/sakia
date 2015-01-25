'''
Created on 2 févr. 2014

@author: inso
'''

import logging
import time
import requests

from ucoinpy.api import bma
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication
from PyQt5.QtCore import QModelIndex, Qt, pyqtSlot, QObject, QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QIcon
from ..gen_resources.currency_tab_uic import Ui_CurrencyTabWidget
from .community_tab import CommunityTabWidget
from ..models.txhistory import HistoryTableModel
from ..models.wallets import WalletsListModel
from ..models.wallet import WalletListModel
from ..tools.exceptions import NoPeerAvailable


class BlockchainWatcher(QObject):
    def __init__(self, account, community):
        super().__init__()
        self.account = account
        self.community = community
        self.exiting = False
        blockid = self.community.current_blockid()
        self.last_block = blockid['number']

    @pyqtSlot()
    def watch(self):
        while not self.exiting:
            time.sleep(10)
            try:
                blockid = self.community.current_blockid()
                block_number = blockid['number']
                if self.last_block != block_number:
                    self.community.refresh_cache()
                    for w in self.account.wallets:
                        w.refresh_cache(self.community)

                    logging.debug("New block, {0} mined in {1}".format(block_number,
                                                                       self.community.currency))
                    self.new_block_mined.emit(block_number)
                    self.last_block = block_number
            except NoPeerAvailable:
                return
            except requests.exceptions.RequestException as e:
                self.connection_error.emit("Cannot check new block : {0}".format(str(e)))

    new_block_mined = pyqtSignal(int)
    connection_error = pyqtSignal(str)


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
        self.bc_watcher.connection_error.connect(self.display_error)

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
            blockchain_init = QDateTime()
            blockchain_init.setTime_t(self.community.get_block(1).mediantime)

            blockchain_lastblock = QDateTime()
            blockchain_lastblock.setTime_t(self.community.get_block().mediantime)

            self.date_from.setMinimumDateTime(blockchain_init)
            self.date_from.setDateTime(blockchain_init)
            self.date_from.setMaximumDateTime(blockchain_lastblock)

            self.date_to.setMinimumDateTime(blockchain_init)
            self.date_to.setDateTime(blockchain_lastblock)
            self.date_to.setMaximumDateTime(blockchain_lastblock)

            self.table_history.setModel(
                HistoryTableModel(self.app.current_account, self.community))
            self.table_history.setSortingEnabled(True)
            self.tab_community = CommunityTabWidget(self.app.current_account,
                                                    self.community,
                                                    self.password_asker)
            self.tabs_account.addTab(self.tab_community,
                                     QIcon(':/icons/community_icon'),
                                    "Community")
            blockid = self.community.current_blockid()
            block_number = blockid['number']
            self.status_label.setText("Connected : Block {0}"
                                             .format(block_number))

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

    @pyqtSlot(int)
    def refresh_block(self, block_number):
        if self.list_wallets.model():
            self.list_wallets.model().dataChanged.emit(
                                                 QModelIndex(),
                                                 QModelIndex(),
                                                 [])

        if self.list_wallet_content.model():
            self.list_wallet_content.model().dataChanged.emit(
                                                 QModelIndex(),
                                                 QModelIndex(),
                                                 [])
        if self.table_history.model():
            self.table_history.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])

        if self.tab_community.list_community_members.model():
            self.tab_community.list_community_members.model().dataChanged.emit(
                                                           QModelIndex(),
                                                           QModelIndex(),
                                                           [])

        self.status_label.setText("Connected : Block {0}"
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
        blockid = self.community.current_blockid()
        block_number = blockid['number']
        self.status_label.setText("Connected : Block {0}"
                                         .format(block_number))

    def closeEvent(self, event):
        self.bc_watcher.deleteLater()
        self.watcher_thread.deleteLater()

    def dates_changed(self, datetime):
        ts_from = self.date_from.dateTime().toTime_t()
        ts_to = self.date_to.dateTime().toTime_t()
        if self.table_history.model():
            self.table_history.model().set_period(ts_from, ts_to)
