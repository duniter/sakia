'''
Created on 5 févr. 2014

@author: inso
'''

import datetime
import logging
from ..core.transfer import Transfer, Received
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale
from PyQt5.QtGui import QFont, QColor


class TxFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, ts_from, ts_to, parent=None):
        super().__init__(parent)
        self.community = None
        self.account = None
        self.ts_from = ts_from
        self.ts_to = ts_to
        # total by column
        self.payments = 0
        self.deposits = 0

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
        date_col = source_model.column_types.index('date')
        source_index = source_model.index(sourceRow, date_col)
        date = source_model.data(source_index, Qt.DisplayRole)
        if in_period(date):
            # calculate sum total payments
            payment = source_model.data(
                source_model.index(sourceRow, source_model.column_types.index('payment')),
                Qt.DisplayRole
            )
            if payment:
                self.payments += int(payment)
            # calculate sum total deposits
            deposit = source_model.data(
                source_model.index(sourceRow, source_model.column_types.index('deposit')),
                Qt.DisplayRole
            )
            if deposit:
                self.deposits += int(deposit)

        return in_period(date)

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None) - 1

    def setSourceModel(self, sourceModel):
        self.community = sourceModel.community
        self.account = sourceModel.account
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

        return (left_data < right_data)

    def data(self, index, role):
        source_index = self.mapToSource(index)
        model = self.sourceModel()
        source_data = model.data(source_index, role)
        state_col = model.column_types.index('state')
        state_index = model.index(source_index.row(), state_col)
        state_data = model.data(state_index, Qt.DisplayRole)
        if role == Qt.DisplayRole:
            if source_index.column() == model.column_types.index('uid'):
                return source_data
            if source_index.column() == model.column_types.index('date'):
                date = QDateTime.fromTime_t(source_data)
                return date.date()
            if source_index.column() == model.column_types.index('payment') or \
                    source_index.column() == model.column_types.index('deposit'):
                if source_data is not "":
                    amount_ref = self.account.units_to_diff_ref(source_data,
                                                                self.community)
                    if isinstance(amount_ref, int):
                        return QLocale().toString(amount_ref)
                    else:
                        return QLocale().toString(amount_ref, 'f', 2)

        if role == Qt.FontRole:
            font = QFont()
            if state_data == Transfer.AWAITING:
                font.setItalic(True)
            elif state_data == Transfer.REFUSED:
                font.setItalic(True)
            elif state_data == Transfer.TO_SEND:
                font.setBold(True)
            else:
                font.setItalic(False)
            return font

        if role == Qt.ForegroundRole:
            if state_data == Transfer.REFUSED:
                return QColor(Qt.red)
            elif state_data == Transfer.TO_SEND:
                return QColor(Qt.blue)

        if role == Qt.TextAlignmentRole:
            if source_index.column() == self.sourceModel().column_types.index(
                    'deposit') or source_index.column() == self.sourceModel().column_types.index('payment'):
                return Qt.AlignRight | Qt.AlignVCenter
            if source_index.column() == self.sourceModel().column_types.index('date'):
                return Qt.AlignCenter

        if role == Qt.ToolTipRole:
            if source_index.column() == self.sourceModel().column_types.index('date'):
                return QDateTime.fromTime_t(source_data).toString(Qt.SystemLocaleLongDate)

        return source_data


class HistoryTableModel(QAbstractTableModel):
    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, account, community, parent=None):
        '''
        Constructor
        '''
        super().__init__(parent)
        self.account = account
        self.community = community
        self.account.referential
        self.transfers_data = []
        self.refresh_transfers()

        self.column_types = (
            'date',
            'uid',
            'payment',
            'deposit',
            'comment',
            'state'
        )

        self.column_headers = (
            self.tr('Date'),
            self.tr('UID/Public key'),
            self.tr('Payment'),
            self.tr('Deposit'),
            self.tr('Comment'),
            self.tr('State')
        )

    @property
    def transfers(self):
        return self.account.transfers(self.community)

    def data_received(self, transfer):
        amount = transfer.metadata['amount']
        comment = ""
        if transfer.txdoc:
            comment = transfer.txdoc.comment
        if transfer.metadata['issuer_uid'] != "":
            sender = transfer.metadata['issuer_uid']
        else:
            sender = "pub:{0}".format(transfer.metadata['issuer'][:5])

        date_ts = transfer.metadata['time']

        return (date_ts, sender, "", amount,
                comment, transfer.state)

    def data_sent(self, transfer):
        amount = transfer.metadata['amount']
        comment = ""
        if transfer.txdoc:
            comment = transfer.txdoc.comment
        if transfer.metadata['receiver_uid'] != "":
            receiver = transfer.metadata['receiver_uid']
        else:
            receiver = "pub:{0}".format(transfer.metadata['receiver'][:5])


        date_ts = transfer.metadata['time']

        return (date_ts, receiver, amount,
                "", comment, transfer.state)

    def refresh_transfers(self):
        self.beginResetModel()
        self.transfers_data = []
        for transfer in self.transfers:
            if type(transfer) is Received:
                self.transfers_data.append(self.data_received(transfer))
            else:
                self.transfers_data.append(self.data_sent(transfer))
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.transfers)

    def columnCount(self, parent):
        return len(self.column_types)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if self.column_types[section] == 'payment' or self.column_types[section] == 'deposit':
                return '{:}\n({:})'.format(
                    self.column_headers[section],
                    self.account.diff_ref_name(self.community.short_currency)
                )

            return self.column_headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self.transfers_data[row][col]

        if role == Qt.ToolTipRole and col == 0:
            return self.transfers[row].metadata['time']

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

