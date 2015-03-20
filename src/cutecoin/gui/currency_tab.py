'''
Created on 2 févr. 2014

@author: inso
'''

import time
import logging
from PyQt5.QtWidgets import QWidget, QMenu, QAction, QApplication, \
                            QMessageBox, QDialog, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QModelIndex, Qt, pyqtSlot, \
                        QThread, QDateTime
from PyQt5.QtGui import QIcon, QCursor
from ..gen_resources.currency_tab_uic import Ui_CurrencyTabWidget
from .community_tab import CommunityTabWidget
from .transfer import TransferMoneyDialog
from .wallets_tab import WalletsTabWidget
from .network_tab import NetworkTabWidget
from ..models.txhistory import HistoryTableModel, TxFilterProxyModel
from .informations_tab import InformationsTabWidget
from ..tools.exceptions import MembershipNotFoundError
from ..core.wallet import Wallet
from ..core.person import Person
from ..core.transfer import Transfer
from cutecoin.core.watching.blockchain import BlockchainWatcher
from cutecoin.core.watching.persons import PersonsWatcher


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
        self.tab_wallets = WalletsTabWidget(self.app,
                                            self.app.current_account,
                                            self.community,
                                            self.password_asker)

        self.tab_network = NetworkTabWidget(self.community)

        self.community.new_block_mined.connect(self.refresh_block)
        persons_watcher = self.app.monitor.persons_watcher(self.community)
        persons_watcher.person_changed.connect(self.tab_community.refresh_person)
        bc_watcher = self.app.monitor.blockchain_watcher(self.community)
        bc_watcher.error.connect(self.display_error)

        person = Person.lookup(self.app.current_account.pubkey, self.community)
        try:
            join_block = person.membership(self.community)['blockNumber']
            join_date = self.community.get_block(join_block).mediantime
            parameters = self.community.parameters
            expiration_date = join_date + parameters['sigValidity']
            current_time = time.time()
            sig_validity = self.community.parameters['sigValidity']
            warning_expiration_time = int(sig_validity / 3)
            will_expire_soon = (current_time > expiration_date - warning_expiration_time)

            if will_expire_soon:
                days = QDateTime().currentDateTime().daysTo(QDateTime.fromTime_t(expiration_date))
                if days > 0:
                    QMessageBox.warning(
                        self,
                        "Membership expiration",
                        "Warning : Membership expiration in {0} days".format(days),
                        QMessageBox.Ok
                    )
        except MembershipNotFoundError as e:
            pass

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

            self.tab_wallets = WalletsTabWidget(self.app,
                                                self.app.current_account,
                                                self.community,
                                                self.password_asker)
            self.tabs_account.addTab(self.tab_wallets,
                                     QIcon(':/icons/wallet_icon'),
                                    "Wallets")

            self.tab_informations = InformationsTabWidget(self.app.current_account,
                                                    self.community)
            self.tabs_account.addTab(self.tab_informations,
                                     QIcon(':/icons/informations_icon'),
                                    "Informations")

            # fix bug refresh_nodes launch on destroyed NetworkTabWidget
            logging.debug('Disconnect community.network.nodes_changed')
            try:
                self.community.network.nodes_changed.disconnect()
            except TypeError:
                logging.debug('No signals on community.network.nodes_changed')

            self.tab_network = NetworkTabWidget(self.community)
            self.tabs_account.addTab(self.tab_network,
                                     QIcon(":/icons/network_icon"),
                                     "Network")
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
        if self.tab_wallets:
            self.tab_wallets.refresh()

        if self.table_history.model():
            self.table_history.model().dataChanged.emit(
                                                     QModelIndex(),
                                                     QModelIndex(),
                                                     [])

        self.persons_watcher_thread.start()

        text = "Connected : Block {0}".format(block_number)
        self.status_label.setText(text)

    def refresh_wallets(self):
        if self.app.current_account:
            self.tab_wallets.refresh()

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
            menu.exec_(QCursor.pos())

    def history_context_menu(self, point):
        index = self.table_history.indexAt(point)
        model = self.table_history.model()
        if index.row() < model.rowCount(QModelIndex()):
            menu = QMenu("Actions", self)
            source_index = model.mapToSource(index)
            state_col = model.sourceModel().column_types.index('state')
            state_index = model.sourceModel().index(source_index.row(),
                                                   state_col)
            state_data = model.sourceModel().data(state_index, Qt.DisplayRole)

            pubkey_col = model.sourceModel().column_types.index('uid')
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
            menu.exec_(QCursor.pos())

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
        dialog.combo_community.setCurrentText(self.community.name)
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

    def showEvent(self, event):
        blockid = self.community.current_blockid()
        block_number = blockid['number']
        self.status_label.setText("Connected : Block {0}"
                                         .format(block_number))

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

        if self.tab_wallets:
            self.tab_wallets.refresh()

        if self.tab_informations:
            self.tab_informations.refresh()
