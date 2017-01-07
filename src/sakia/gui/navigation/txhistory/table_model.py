"""
Created on 5 févr. 2014

@author: inso
"""

import asyncio
import datetime
import logging
import math

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale, QModelIndex
from PyQt5.QtGui import QFont, QColor, QIcon
from sakia.errors import NoPeerAvailable
from sakia.data.entities import Transaction
from sakia.constants import MAX_CONFIRMATIONS
from sakia.decorators import asyncify, once_at_a_time, cancel_once_task


class TxFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent, ts_from, ts_to, blockchain_service):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        :param int ts_from: the min timestamp of latest tx
        :param in ts_to: the max timestamp of most recent tx
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        """
        super().__init__(parent)
        self.app = None
        self.ts_from = ts_from
        self.ts_to = ts_to
        self.blockchain_service = blockchain_service

    def set_period(self, ts_from, ts_to):
        """
        Filter table by given timestamps
        """
        logging.debug("Filtering from {0} to {1}".format(
            datetime.datetime.fromtimestamp(ts_from).isoformat(' '),
            datetime.datetime.fromtimestamp(ts_to).isoformat(' '))
        )
        self.beginResetModel()
        self.ts_from = ts_from
        self.ts_to = ts_to
        self.endResetModel()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        def in_period(date_ts):
            return date_ts in range(self.ts_from, self.ts_to)

        source_model = self.sourceModel()
        date_col = source_model.columns_types.index('date')
        source_index = source_model.index(sourceRow, date_col)
        date = source_model.data(source_index, Qt.DisplayRole)
        if in_period(date):
            # calculate sum total payments
            payment = source_model.data(
                source_model.index(sourceRow, source_model.columns_types.index('amount')),
                Qt.DisplayRole
            )

        return in_period(date)

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None) - 5

    def setSourceModel(self, source_model):
        self.app = source_model.app
        super().setSourceModel(source_model)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        source_model = self.sourceModel()
        left_data = source_model.data(left, Qt.DisplayRole)
        right_data = source_model.data(right, Qt.DisplayRole)
        if left_data == "":
            return self.sortOrder() == Qt.DescendingOrder
        elif right_data == "":
            return self.sortOrder() == Qt.AscendingOrder
        if left_data == right_data:
            txid_col = source_model.columns_types.index('txid')
            txid_left = source_model.index(left.row(), txid_col)
            txid_right = source_model.index(right.row(), txid_col)
            return (txid_left < txid_right)

        return (left_data < right_data)

    def data(self, index, role):
        source_index = self.mapToSource(index)
        model = self.sourceModel()
        source_data = model.data(source_index, role)
        state_col = model.columns_types.index('state')
        state_index = model.index(source_index.row(), state_col)
        state_data = model.data(state_index, Qt.DisplayRole)

        block_col = model.columns_types.index('block_number')
        block_index = model.index(source_index.row(), block_col)
        block_data = model.data(block_index, Qt.DisplayRole)

        if state_data == Transaction.VALIDATED:
            current_confirmations = self.blockchain_service.current_buid().number - block_data
        else:
            current_confirmations = 0

        if role == Qt.DisplayRole:
            if source_index.column() == model.columns_types.index('uid'):
                return source_data
            if source_index.column() == model.columns_types.index('date'):
                return QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(source_data).date(),
                    QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                )
            if source_index.column() == model.columns_types.index('amount'):
                amount = self.app.current_ref.instance(source_data, model.connection.currency, self.app, block_data) \
                    .diff_localized(international_system=self.app.parameters.international_system_of_units)
                return amount

        if role == Qt.FontRole:
            font = QFont()
            if state_data == Transaction.AWAITING or \
                    (state_data == Transaction.VALIDATED and current_confirmations < MAX_CONFIRMATIONS):
                font.setItalic(True)
            elif state_data == Transaction.REFUSED:
                font.setItalic(True)
            elif state_data == Transaction.TO_SEND:
                font.setBold(True)
            else:
                font.setItalic(False)
            return font

        if role == Qt.ForegroundRole:
            if state_data == Transaction.REFUSED:
                return QColor(Qt.darkGray)
            elif state_data == Transaction.TO_SEND:
                return QColor(Qt.blue)
            if source_index.column() == model.columns_types.index('amount'):
                if source_data < 0:
                    return QColor(Qt.darkRed)
                elif state_data == HistoryTableModel.DIVIDEND:
                    return QColor(Qt.darkBlue)

        if role == Qt.TextAlignmentRole:
            if self.sourceModel().columns_types.index('amount'):
                return Qt.AlignRight | Qt.AlignVCenter
            if source_index.column() == model.columns_types.index('date'):
                return Qt.AlignCenter

        if role == Qt.ToolTipRole:
            if source_index.column() == model.columns_types.index('date'):
                return QDateTime.fromTime_t(source_data).toString(Qt.SystemLocaleLongDate)

            if state_data == Transaction.VALIDATED or state_data == Transaction.AWAITING:
                if current_confirmations >= MAX_CONFIRMATIONS:
                    return None
                elif self.app.parameters.expert_mode:
                    return self.tr("{0} / {1} confirmations").format(current_confirmations, MAX_CONFIRMATIONS)
                else:
                    confirmation = current_confirmations / MAX_CONFIRMATIONS * 100
                    confirmation = 100 if confirmation > 100 else confirmation
                    return self.tr("Confirming... {0} %").format(QLocale().toString(float(confirmation), 'f', 0))

            return None
        return source_data


class HistoryTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display communities in a tree
    """

    DIVIDEND = 32

    def __init__(self, parent, app, connection, identities_service, transactions_service):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        :param sakia.app.Application app: the main application
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.services.IdentitiesService identities_service: the identities service
        :param sakia.services.TransactionsService transactions_service: the transactions service
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.identities_service = identities_service
        self.transactions_service = transactions_service
        self.transfers_data = []

        self.columns_types = (
            'date',
            'uid',
            'amount',
            'comment',
            'state',
            'txid',
            'pubkey',
            'block_number',
            'txhash'
        )

        self.column_headers = (
            lambda: self.tr('Date'),
            lambda: self.tr('UID/Public key'),
            lambda: self.tr('Amount'),
            lambda: self.tr('Comment')
        )

    def transfers(self):
        """
        Transfer
        :rtype: List[sakia.data.entities.Transfer]
        """
        return self.transactions_service.transfers(self.connection.pubkey)

    def dividends(self):
        """
        Transfer
        :rtype: List[sakia.data.entities.Dividend]
        """
        return self.transactions_service.dividends(self.connection.pubkey)

    def add_transfer(self, transfer):
        self.beginInsertRows(QModelIndex(), 0, 0)
        if isinstance(transfer, Transaction):
            if transfer.issuer == self.connection.pubkey:
                self.transfers_data.append(self.data_sent(transfer))
            else:
                self.transfers_data.append(self.data_received(transfer))
        self.endInsertRows()

    def change_transfer(self, transfer):
        if isinstance(transfer, Transaction):
            for i, data in enumerate(self.transfers_data):
                if data[self.columns_types.index('txhash')] == transfer.sha_hash:
                    if transfer.issuer == self.connection.pubkey:
                        self.transfers_data[self.columns_types.index('txhash')] = self.data_sent(transfer)
                    else:
                        self.transfers_data[self.columns_types.index('txhash')] = self.data_received(transfer)
                    self.dataChanged.emit(self.index(i, 0), self.index(i, len(self.columns_types)))
                    return

    def data_received(self, transfer):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Transaction transfer: the transaction
        :return: data as tuple
        """
        block_number = transfer.written_block

        amount = transfer.amount * 10**transfer.amount_base

        identity = self.identities_service.get_identity(transfer.issuer)
        if identity:
            sender = identity.uid
        else:
            sender = transfer.issuer

        date_ts = transfer.timestamp
        txid = transfer.txid

        return (date_ts, sender, amount,
                transfer.comment, transfer.state, txid,
                transfer.issuer, block_number, transfer.sha_hash)

    def data_sent(self, transfer):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Transaction transfer: the transaction
        :return: data as tuple
        """
        block_number = transfer.written_block

        amount = transfer.amount * 10**transfer.amount_base * -1
        identity = self.identities_service.get_identity(transfer.receiver)
        if identity:
            receiver = identity.uid
        else:
            receiver = transfer.receiver

        date_ts = transfer.timestamp
        txid = transfer.txid
        return (date_ts, receiver, amount, transfer.comment, transfer.state, txid,
                transfer.receiver, block_number, transfer.sha_hash)

    def data_dividend(self, dividend):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Dividend dividend: the dividend
        :return: data as tuple
        """
        block_number = dividend.block_number

        amount = dividend.amount * 10**dividend.base
        identity = self.identities_service.get_identity(dividend.pubkey)
        if identity:
            receiver = identity.uid
        else:
            receiver = dividend.pubkey

        date_ts = dividend.timestamp
        return (date_ts, receiver, amount, "", HistoryTableModel.DIVIDEND, 0,
                receiver, block_number, "")

    def init_transfers(self):
        self.beginResetModel()
        self.transfers_data = []
        transfers = self.transfers()
        for transfer in transfers:
            if transfer.issuer == self.connection.pubkey:
                self.transfers_data.append(self.data_sent(transfer))
            else:
                self.transfers_data.append(self.data_received(transfer))
        dividends = self.dividends()
        for dividend in dividends:
            self.transfers_data.append(self.data_dividend(dividend))
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.transfers_data)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if self.columns_types[section] == 'payment' or self.columns_types[section] == 'deposit':
                return '{:}\n({:})'.format(
                    self.column_headers[section](),
                    self.app.current_ref.instance(0, self.connection.currency, self.app, None).diff_units
                )

            return self.column_headers[section]()

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        if role in (Qt.DisplayRole, Qt.ForegroundRole, Qt.ToolTipRole):
            return self.transfers_data[row][col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

