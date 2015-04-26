from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QDialog, \
    QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QDateTime, QModelIndex
from PyQt5.QtGui import QCursor
from ..gen_resources.transactions_tab_uic import Ui_transactionsTabWidget
from ..models.txhistory import HistoryTableModel, TxFilterProxyModel
from ..core.transfer import Transfer
from ..core.wallet import Wallet
from ..core.person import Person
from .transfer import TransferMoneyDialog

import logging

class TransactionsTabWidget(QWidget, Ui_transactionsTabWidget):
    """
    classdocs
    """

    def __init__(self, app, community, password_asker, currency_tab):
        """
        Constructor
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community
        self.password_asker = password_asker
        self.currency_tab = currency_tab
        self.refresh()

    def refresh(self):
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
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

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
        dialog.accepted.connect(self.currency_tab.refresh_wallets)
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

    def dates_changed(self):
        logging.debug("Changed dates")
        if self.table_history.model():
            ts_from = self.date_from.dateTime().toTime_t()
            ts_to = self.date_to.dateTime().toTime_t()

            self.table_history.model().set_period(ts_from, ts_to)


