"""
Created on 5 févr. 2014

@author: inso
"""

import datetime
import logging
import asyncio
from ..core.transfer import Transfer, TransferState
from ..core.net.network import MAX_CONFIRMATIONS
from ..tools.exceptions import NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale, QModelIndex

from PyQt5.QtGui import QFont, QColor, QIcon


class TxFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, ts_from, ts_to, parent=None):
        super().__init__(parent)
        self.app = None
        self.ts_from = ts_from
        self.ts_to = ts_to
        self.payments = 0
        self.deposits = 0

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
            if state_data == TransferState.AWAITING or state_data == TransferState.VALIDATING:
                font.setItalic(True)
            elif state_data == TransferState.REFUSED:
                font.setItalic(True)
            elif state_data == TransferState.TO_SEND:
                font.setBold(True)
            else:
                font.setItalic(False)
            return font

        if role == Qt.ForegroundRole:
            if state_data == TransferState.REFUSED:
                return QColor(Qt.red)
            elif state_data == TransferState.TO_SEND:
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

            if state_data == TransferState.VALIDATING or state_data == TransferState.AWAITING:
                block_col = model.columns_types.index('block_number')
                block_index = model.index(source_index.row(), block_col)
                block_data = model.data(block_index, Qt.DisplayRole)

                current_confirmations = 0
                if state_data == TransferState.VALIDATING:
                    current_blockid_number = self.community.network.current_blockid.number
                    if current_blockid_number:
                        current_confirmations = current_blockid_number - block_data
                elif state_data == TransferState.AWAITING:
                    current_confirmations = 0

                max_confirmations = self.sourceModel().max_confirmations()

                if self.app.preferences['expert_mode']:
                    return self.tr("{0} / {1} confirmations").format(current_confirmations, max_confirmations)
                else:
                    confirmation = current_confirmations / max_confirmations * 100
                    confirmation = 100 if confirmation > 100 else confirmation
                    return self.tr("Confirming... {0} %").format(QLocale().toString(float(confirmation), 'f', 0))

            return None
        return source_data


class HistoryTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display communities in a tree
    """

    def __init__(self, app, account, community, parent=None):
        """
        Constructor
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
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

    def change_account(self, account):
        cancel_once_task(self, self.refresh_transfers)
        self.account = account

    def change_community(self, community):
        cancel_once_task(self, self.refresh_transfers)
        self.community = community

    def transfers(self):
        if self.account:
            return self.account.transfers(self.community) + self.account.dividends(self.community)
        else:
            return []

    async def data_received(self, transfer):
        amount = transfer.metadata['amount']
        if transfer.blockid:
            block_number = transfer.blockid.number
        else:
            block_number = None
        try:
            deposit = await self.account.current_ref(transfer.metadata['amount'], self.community,
                                                     self.app, block_number)\
                .diff_localized(international_system=self.app.preferences['international_system_of_units'])
        except NoPeerAvailable:
            deposit = "Could not compute"
        comment = ""
        if transfer.metadata['comment'] != "":
            comment = transfer.metadata['comment']
        if transfer.metadata['issuer_uid'] != "":
            sender = transfer.metadata['issuer_uid']
        else:
            sender = "pub:{0}".format(transfer.metadata['issuer'][:5])

        date_ts = transfer.metadata['time']
        txid = transfer.metadata['txid']

        return (date_ts, sender, "", deposit,
                comment, transfer.state, txid,
                transfer.metadata['issuer'], block_number, amount)

    async def data_sent(self, transfer):
        if transfer.blockid:
            block_number = transfer.blockid.number
        else:
            block_number = None

        amount = transfer.metadata['amount']
        try:
            paiment = await self.account.current_ref(transfer.metadata['amount'], self.community,
                                                     self.app, block_number)\
                .diff_localized(international_system=self.app.preferences['international_system_of_units'])
        except NoPeerAvailable:
            paiment = "Could not compute"
        comment = ""
        if transfer.metadata['comment'] != "":
            comment = transfer.metadata['comment']
        if transfer.metadata['receiver_uid'] != "":
            receiver = transfer.metadata['receiver_uid']
        else:
            receiver = "pub:{0}".format(transfer.metadata['receiver'][:5])

        date_ts = transfer.metadata['time']
        txid = transfer.metadata['txid']
        return (date_ts, receiver, paiment,
                "", comment, transfer.state, txid,
                transfer.metadata['receiver'], block_number, amount)

    async def data_dividend(self, dividend):
        amount = dividend['amount']
        try:
            deposit = await self.account.current_ref(dividend['amount'], self.community, self.app, dividend['block_number'])\
                .diff_localized(international_system=self.app.preferences['international_system_of_units'])
        except NoPeerAvailable:
            deposit = "Could not compute"
        comment = ""
        receiver = self.account.name
        date_ts = dividend['time']
        id = dividend['id']
        block_number = dividend['block_number']
        state = dividend['state']

        return (date_ts, receiver, "",
                deposit, "", state, id,
                self.account.pubkey, block_number, amount)

    @once_at_a_time
    @asyncify
    async def refresh_transfers(self):
        self.beginResetModel()
        self.transfers_data = []
        self.endResetModel()
        self.beginResetModel()
        transfers_data = []
        if self.community:
            requests_coro = []
            data_list = []
            count = 0
            transfers = self.transfers()
            for transfer in transfers:
                coro = None
                count += 1
                if type(transfer) is Transfer:
                    if transfer.metadata['issuer'] == self.account.pubkey:
                        coro = asyncio.ensure_future(self.data_sent(transfer))
                    else:
                        coro = asyncio.ensure_future(self.data_received(transfer))
                elif type(transfer) is dict:
                    coro = asyncio.ensure_future(self.data_dividend(transfer))
                if coro:
                    requests_coro.append(coro)
                if count % 25 == 0:
                    gathered_list = await asyncio.gather(*requests_coro)
                    requests_coro = []
                    data_list.extend(gathered_list)
            # One last gathering
            gathered_list = await asyncio.gather(*requests_coro)
            data_list.extend(gathered_list)

            for data in data_list:
                transfers_data.append(data)
        self.transfers_data = transfers_data
        self.endResetModel()

    def max_confirmations(self):
        return MAX_CONFIRMATIONS

    def rowCount(self, parent):
        return len(self.transfers_data)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if self.account and self.community:
            if role == Qt.DisplayRole:
                if self.columns_types[section] == 'payment' or self.columns_types[section] == 'deposit':
                    return '{:}\n({:})'.format(
                        self.column_headers[section](),
                        self.account.current_ref(0, self.community, self.app, None).diff_units
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

