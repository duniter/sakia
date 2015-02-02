'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.transfer import Transfer, Received
from ..core.person import Person
from ..tools.exceptions import PersonNotFoundError
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
                        QDateTime, QModelIndex
from PyQt5.QtGui import QFont


class TxFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, community, ts_from, ts_to, parent=None):
        super().__init__(parent)
        self.community = community
        self.ts_from = ts_from
        self.ts_to = ts_to

    def set_period(self, ts_from, ts_to):
        """
        Filter table by given timestamps
        """
        logging.debug("Filtering from {0} to {1}".format(ts_from, ts_to))
        self.ts_from = ts_from
        self.ts_to = ts_to

    def filterAcceptsRow(self, sourceRow, sourceParent):
        def in_period(date):
            return (QDateTime(date).toTime_t() in range(self.ts_from, self.ts_to))

        date_col = self.sourceModel().columns.index('Date')
        source_index = self.sourceModel().index(sourceRow, date_col)
        date = self.sourceModel().data(source_index, Qt.DisplayRole)
        return in_period(date)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        return (left_data < right_data)

    def data(self, index, role):
        source_index = self.mapToSource(index)
        source_data = self.sourceModel().data(source_index, role)
        if role == Qt.DisplayRole:
            if source_index.column() == self.sourceModel().columns.index('UID/Public key'):
                if source_data.__class__ == Person:
                    tx_person = source_data.name
                else:
                    tx_person = "pub:{0}".format(source_data[:5])
                source_data = tx_person
                return source_data
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
        self.columns = ('Date', 'UID/Public key', 'Payment', 'Deposit', 'Comment')

    @property
    def transfers(self):
        return self.account.transfers(self.community)

    def rowCount(self, parent):
        return len(self.transfers)

    def columnCount(self, parent):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.columns[section]

    def data_received(self, transfer):
        amount = transfer.metadata['amount']
        comment = transfer.txdoc.comment
        pubkey = transfer.metadata['issuer']
        try:
            #sender = Person.lookup(pubkey, self.community).name
            sender = Person.lookup(pubkey, self.community)
        except PersonNotFoundError:
            #sender = "pub:{0}".format(pubkey[:5])
            sender = pubkey

        date_ts = transfer.metadata['time']
        date = QDateTime.fromTime_t(date_ts)

        amount_ref = self.account.units_to_ref(amount, self.community)
        ref_name = self.account.ref_name(self.community.short_currency)

        return (date.date(), sender, "", "{0:.2f} {1}".format(amount_ref, ref_name),
                comment)

    def data_sent(self, transfer):
        amount = transfer.metadata['amount']

        comment = transfer.txdoc.comment
        pubkey = transfer.metadata['receiver']
        try:
            #receiver = Person.lookup(pubkey, self.community).name
            receiver = Person.lookup(pubkey, self.community)
        except PersonNotFoundError:
            #receiver = "pub:{0}".format(pubkey[:5])
            receiver = pubkey

        date_ts = transfer.metadata['time']
        date = QDateTime.fromTime_t(date_ts)

        amount_ref = self.account.units_to_ref(-amount, self.community)
        ref_name = self.account.ref_name(self.community.short_currency)

        return (date.date(), receiver, "{0:.2f} {1}".format(amount_ref, ref_name),
                "", comment)

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        transfer = self.transfers[row]
        if role == Qt.DisplayRole:
            if type(transfer) is Received:
                return self.data_received(transfer)[col]
            else:
                return self.data_sent(transfer)[col]

        if role == Qt.FontRole:
            font = QFont()
            if transfer.state == Transfer.AWAITING:
                font.setItalic(True)
            else:
                font.setItalic(False)
            return font

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
