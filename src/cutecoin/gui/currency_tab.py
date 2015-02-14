'''
Created on 2 févr. 2014

@author: inso
'''

import logging
import time
import requests

from ucoinpy.api import bma
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication, \
                            QMessageBox, QDialog, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QModelIndex, Qt, pyqtSlot, QObject, \
                        QThread, pyqtSignal, QDateTime
from PyQt5.QtGui import QIcon
from ..gen_resources.currency_tab_uic import Ui_CurrencyTabWidget
from .community_tab import CommunityTabWidget
from .transfer import TransferMoneyDialog
from ..models.txhistory import HistoryTableModel, TxFilterProxyModel
from .informations_tab import InformationsTabWidget
from ..models.wallets import WalletsListModel
from ..models.wallet import WalletListModel
from ..tools.exceptions import NoPeerAvailable
from ..core.wallet import Wallet
from ..core.person import Person
from ..core.transfer import Transfer


class BlockchainWatcher(QObject):
    def __init__(self, account, community):
        super().__init__()
        self.account = account
        self.community = community
        self.time_to_wait = int(self.community.get_parameters()['avgGenTime'] / 10)
        self.exiting = False
        blockid = self.community.current_blockid()
        self.last_block = blockid['number']

    @pyqtSlot()
    def watch(self):
        while not self.exiting:
            time.sleep(self.time_to_wait)
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

            self.date_from.setMinimumDateTime(blockchain_init)
            self.date_from.setDateTime(blockchain_init)
            self.date_from.setMaximumDateTime(QDateTime().currentDateTime())

            self.date_to.setMinimumDateTime(blockchain_init)
            tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
            self.date_to.setDateTime(tomorrow_datetime)
            self.date_to.setMaximumDateTime(tomorrow_datetime)

            ts_from = self.date_from.dateTime().toTime_t()
            ts_to = self.date_to.dateTime().toTime_t()

            model = HistoryTableModel(self.app.current_account, self.community)
            proxy = TxFilterProxyModel(ts_from, ts_to)
            proxy.setSourceModel(model)
            proxy.setDynamicSortFilter(True)
            proxy.setSortRole(Qt.DisplayRole)

            self.table_history.setModel(proxy)
            self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.table_history.setSortingEnabled(True)
            self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.tab_community = CommunityTabWidget(self.app.current_account,
                                                    self.community,
                                                    self.password_asker)
            self.tabs_account.addTab(self.tab_community,
                                     QIcon(':/icons/community_icon'),
                                    "Community")
            self.tab_informations = InformationsTabWidget(self.app.current_account,
                                                    self.community)
            self.tabs_account.addTab(self.tab_informations,
                                     QIcon(':/icons/informations_icon'),
                                    "Informations")
            self.tab_informations.refresh()
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

        if self.tab_community.table_community_members.model():
            self.tab_community.table_community_members.model().dataChanged.emit(
                                                           QModelIndex(),
                                                           QModelIndex(),
                                                           [])

        person = Person.lookup(self.app.current_account.pubkey, self.community)
        join_block = person.membership(self.community).block_number
        join_date = self.community.get_block(join_block).mediantime
        parameters = self.community.get_parameters()
        expiration_date = join_date + parameters['sigValidity']
        current_time = time.time()
        sig_validity = self.community.get_parameters()['sigValidity']
        warning_expiration_time = int(sig_validity / 3)
        will_expire_soon = (current_time > expiration_date - warning_expiration_time)
        text = "Connected : Block {0}".format(block_number)
        self.status_label.setText(text)

        if will_expire_soon:
            days = QDateTime().currentDateTime().daysTo(QDateTime.fromTime_t(expiration_date))
            QMessageBox.warning(
                self,
                "Membership expiration",
                "Warning : Membership expiration in {0} days".format(days),
                QMessageBox.Ok
            )

    def refresh_wallets(self):
        if self.app.current_account:
            wallets_list_model = WalletsListModel(self.app.current_account,
                                                  self.community)
            wallets_list_model.dataChanged.connect(self.wallet_changed)
            self.list_wallets.setModel(wallets_list_model)
            self.refresh_wallet_content(QModelIndex())

    def refresh_wallet_content(self, index):
        if self.app.current_account:
            current_wallet = self.app.current_account.wallets[index.row()]
            wallet_list_model = WalletListModel(current_wallet, self.community)
            self.list_wallet_content.setModel(wallet_list_model)

    def wallet_context_menu(self, point):
        index = self.list_wallets.indexAt(point)
        model = self.list_wallets.model()
        if index.row() < model.rowCount(QModelIndex()):
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

    def history_context_menu(self, point):
        index = self.table_history.indexAt(point)
        model = self.table_history.model()
        if index.row() < model.rowCount(QModelIndex()):
            menu = QMenu("Actions", self)
            source_index = model.mapToSource(index)
            state_col = model.sourceModel().columns.index('State')
            state_index = model.sourceModel().index(source_index.row(),
                                                   state_col)
            state_data = model.sourceModel().data(state_index, Qt.DisplayRole)

            pubkey_col = model.sourceModel().columns.index('UID/Public key')
            person_index = model.sourceModel().index(source_index.row(),
                                                    pubkey_col)
            person = model.sourceModel().data(person_index, Qt.DisplayRole)
            transfer = model.sourceModel().transfers[source_index.row()]
            if state_data == Transfer.REFUSED or state_data == Transfer.TO_SEND:
                send_back = QAction("Send again", self)
                send_back.triggered.connect(self.send_again)
                send_back.setData(transfer)
                menu.addAction(send_back)

                cancel = QAction("Cancel", self)
                cancel.triggered.connect(self.cancel_transfer)
                cancel.setData(transfer)
                menu.addAction(cancel)

            copy_pubkey = QAction("Copy pubkey to clipboard", self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(person)
            menu.addAction(copy_pubkey)
            # Show the context menu.
            menu.exec_(self.table_history.mapToGlobal(point))

    def rename_wallet(self):
        index = self.sender().data()
        self.list_wallets.edit(index)

    def copy_pubkey_to_clipboard(self):
        data = self.sender().data()
        clipboard = QApplication.clipboard()
        if data.__class__ is Wallet:
            clipboard.setText(data.pubkey)
        elif data.__class__ is Person:
            clipboard.setText(data.pubkey)
        elif data.__class__ is str:
            clipboard.setText(data)

    def send_again(self):
        transfer = self.sender().data()
        dialog = TransferMoneyDialog(self.app.current_account,
                                     self.password_asker)
        dialog.accepted.connect(self.refresh_wallets)
        sender = transfer.metadata['issuer']
        wallet_index = [w.pubkey for w in self.app.current_account.wallets].index(sender)
        dialog.combo_wallets.setCurrentIndex(wallet_index)
        dialog.edit_pubkey.setText(transfer.metadata['receiver'])
        dialog.combo_community.setCurrentText(self.community.name())
        dialog.spinbox_amount.setValue(transfer.metadata['amount'])
        dialog.radio_pubkey.setChecked(True)
        dialog.edit_message.setText(transfer.metadata['comment'])
        result = dialog.exec_()
        if result == QDialog.Accepted:
            transfer.drop()
            self.table_history.model().invalidate()

    def cancel_transfer(self):
        reply = QMessageBox.warning(self, "Warning",
                             """Are you sure ?
This money transfer will be removed and not sent.""",
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transfer = self.sender().data()
            transfer.drop()
            self.table_history.model().invalidate()

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
            self.table_history.model().invalidate()

    def referential_changed(self):
        if self.table_history.model():
            self.table_history.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])

        if self.list_wallets.model():
            self.list_wallets.model().dataChanged.emit(
                                                 QModelIndex(),
                                                 QModelIndex(),
                                                 [])
        if self.tab_informations:
            self.tab_informations.refresh()
