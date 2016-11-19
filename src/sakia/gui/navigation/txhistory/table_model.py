"""
Created on 5 févr. 2014

@author: inso
"""

import asyncio
import datetime
import logging
import math

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale
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
        self.payments = 0
        self.deposits = 0
        self.blockchain_service = blockchain_service


    @property
    def account(self):
        return self.app.current_account

    def set_period(self, ts_from, ts_to):
        """
        Filter table by given timestamps
        """
        logging.debug("Filtering from {0} to {1}".format(
            datetime.datetime.fromtimestamp(ts_from).isoformat(' '),
            datetime.datetime.fromtimestamp(ts_to).isoformat(' '))
        )
        self.ts_from = ts_from
        self.ts_to = ts_to
        self.modelReset.emit()

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
            if payment:
                self.payments += int(payment)
            # calculate sum total deposits
            deposit = source_model.data(
                source_model.index(sourceRow, source_model.columns_types.index('amount')),
                Qt.DisplayRole
            )
            if deposit:
                self.deposits += int(deposit)

        return in_period(date)

    @property
    def community(self):
        return self.sourceModel().community

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None) - 5

    def setSourceModel(self, sourceModel):
        self.app = sourceModel.app
        super().setSourceModel(sourceModel)

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
        if role == Qt.DisplayRole:
            if source_index.column() == model.columns_types.index('uid'):
                return source_data
            if source_index.column() == model.columns_types.index('date'):
                return QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(source_data).date(),
                    QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                )
            if source_index.column() == model.columns_types.index('payment') or \
                    source_index.column() == model.columns_types.index('deposit'):
                return source_data

        if role == Qt.FontRole:
            font = QFont()
            if state_data == Transaction.AWAITING or state_data == Transaction.VALIDATING:
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
                return QColor(Qt.red)
            elif state_data == Transaction.TO_SEND:
                return QColor(Qt.blue)

        if role == Qt.TextAlignmentRole:
            if source_index.column() == self.sourceModel().columns_types.index(
                    'deposit') or source_index.column() == self.sourceModel().columns_types.index('payment'):
                return Qt.AlignRight | Qt.AlignVCenter
            if source_index.column() == self.sourceModel().columns_types.index('date'):
                return Qt.AlignCenter

        if role == Qt.ToolTipRole:
            if source_index.column() == self.sourceModel().columns_types.index('date'):
                return QDateTime.fromTime_t(source_data).toString(Qt.SystemLocaleLongDate)

            if state_data == Transaction.VALIDATING or state_data == Transaction.AWAITING:
                block_col = model.columns_types.index('block_number')
                block_index = model.index(source_index.row(), block_col)
                block_data = model.data(block_index, Qt.DisplayRole)

                current_confirmations = 0
                if state_data == Transaction.VALIDATING:
                    current_confirmations = self.blockchain_service.current_buid().number - block_data
                elif state_data == Transaction.AWAITING:
                    current_confirmations = 0

                if self.app.preferences['expert_mode']:
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
        self.refresh_transfers()

        self.columns_types = (
            'date',
            'uid',
            'payment',
            'deposit',
            'comment',
            'state',
            'txid',
            'pubkey',
            'block_number',
            'amount'
        )

        self.column_headers = (
            lambda: self.tr('Date'),
            lambda: self.tr('UID/Public key'),
            lambda: self.tr('Payment'),
            lambda: self.tr('Deposit'),
            lambda: self.tr('Comment'),
            lambda: 'State',
            lambda: 'TXID',
            lambda: 'Pubkey',
            lambda: 'Block Number'
        )

    def transfers(self):
        """
        Transfer
        :rtype: sakia.data.entities.Transfer
        """
        #TODO: Handle dividends
        return self.transactions_service.transfers(self.connection.pubkey)

    def data_received(self, transfer):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Transaction transfer: the transaction
        :return: data as tuple
        """
        if transfer.blockstamp:
            block_number = transfer.blockstamp.number
        else:
            block_number = None

        amount = transfer.amount * 10**transfer.amount_base
        try:
            deposit = self.account.current_ref.instance(amount, self.connection.currency, self.app, block_number)\
                .diff_localized(international_system=self.app.preferences['international_system_of_units'])
        except NoPeerAvailable:
            deposit = "Could not compute"

        identity = self.identities_service.get_identity(transfer.receiver)
        if identity:
            sender = identity.uid
        else:
            sender = "pub:{0}".format(transfer.receiver[:5])

        date_ts = transfer.timestamp
        txid = transfer.txid

        return (date_ts, sender, "", deposit,
                transfer.comment, transfer.state, txid,
                transfer.metadata['issuer'], block_number, amount)

    async def data_sent(self, transfer):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Transaction transfer: the transaction
        :return: data as tuple
        """
        if transfer.blockstamp:
            block_number = transfer.blockstamp.number
        else:
            block_number = None

        amount = transfer.amount * 10**transfer.amount_base
        try:
            paiement = self.app.current_ref.instance(amount, self.connection.currency, self.app, block_number)\
                            .diff_localized(international_system=self.app.parameters.international_system_of_units)
        except NoPeerAvailable:
            paiement = "Could not compute"

        identity = self.identities_service.get_identity(transfer.receiver)
        if identity:
            receiver = identity.uid
        else:
            receiver = "pub:{0}".format(transfer.receiver[:5])

        date_ts = transfer.timestamp
        txid = transfer.txid
        return (date_ts, receiver, paiement,
                "", transfer.comment, transfer.state, txid,
                transfer.receiver, block_number, amount)

    async def data_dividend(self, dividend):
        pass

    def refresh_transfers(self):
        self.beginResetModel()
        transfers_data = []
        data_list = []
        count = 0
        transfers = self.transfers()
        for transfer in transfers:
            count += 1
            if type(transfer) is Transaction:
                if transfer.issuer == self.connection.pubkey:
                    data_list += self.data_sent(transfer)
                else:
                    data_list += self.data_received(transfer)
            elif type(transfer) is dict:
                data_list += self.data_dividend(transfer)

            for data in data_list:
                transfers_data.append(data)
        self.transfers_data = transfers_data
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

        if role == Qt.DisplayRole:
            return self.transfers_data[row][col]

        if role == Qt.ToolTipRole:
            return self.transfers_data[row][col]

        if role == Qt.DecorationRole and index.column() == 0:
            transfer = self.transfers_data[row]
            if transfer[self.columns_types.index('payment')] != "":
                return QIcon(":/icons/sent")
            elif transfer[self.columns_types.index('uid')] == self.account.name:
                return QIcon(":/icons/dividend")
            else:
                return QIcon(":/icons/received")

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

