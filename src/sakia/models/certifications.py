"""
Created on 5 févr. 2014

@author: inso
"""

import datetime
import logging

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale
from PyQt5.QtGui import QFont, QColor

from sakia.decorators import asyncify, once_at_a_time, cancel_once_task


class CertsFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, ts_from, ts_to, parent=None):
        super().__init__(parent)
        self.app = None
        self.ts_from = ts_from
        self.ts_to = ts_to

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
            return font

        if role == Qt.ForegroundRole:
            if state_data == TransferState.REFUSED:
                return QColor(Qt.red)
            elif state_data == TransferState.TO_SEND:
                return QColor(Qt.blue)

        if role == Qt.TextAlignmentRole:
            if source_index.column() == self.sourceModel().columns_types.index('date'):
                return Qt.AlignCenter

        if role == Qt.ToolTipRole:
            if source_index.column() == self.sourceModel().columns_types.index('date'):
                return QDateTime.fromTime_t(source_data).toString(Qt.SystemLocaleLongDate)
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
        self.refresh_certs()
        self._max_confirmations = 0

        self.columns_types = (
            'date',
            'uid',
            'state',
            'pubkey',
            'block_number'
        )

        self.column_headers = (
            self.tr('Date'),
            self.tr('UID/Public key'),
            'State',
            'Pubkey',
            'Block Number'
        )

    def change_account(self, account):
        cancel_once_task(self, self.refresh_certs)
        self.account = account

    def change_community(self, community):
        cancel_once_task(self, self.refresh_certs)
        self.community = community

    def certifications(self):
        if self.account:
            return self.account.certifications(self.community)
        else:
            return []

    @once_at_a_time
    @asyncify
    async def refresh_certs(self):
        self.beginResetModel()
        self.transfers_data = []
        self.endResetModel()

    def max_confirmations(self):
        return self._max_confirmations

    def rowCount(self, parent):
        return len(self.transfers_data)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if self.account and self.community:
            if role == Qt.DisplayRole:
                return self.column_headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            return self.transfers_data[row][col]

        if role == Qt.ToolTipRole:
            return self.transfers_data[row][col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

