'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.person import Person
from ..tools.exceptions import PersonNotFoundError
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, QDateTime
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
        def in_period(tx):
            block = self.community.get_block(tx[0])
            return (block.mediantime in range(self.ts_from, self.ts_to))

        tx = self.sourceModel().transactions[sourceRow]
        return in_period(tx)

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
        self.transactions = self.account.transactions_sent(self.community) + \
         self.account.transactions_awaiting(self.community) + \
         self.account.transactions_received(self.community)

    def rowCount(self, parent):
        return len(self.transactions)

    def columnCount(self, parent):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.columns[section]

    def data_received(self, tx):
        outputs = []
        amount = 0
        for o in tx[1].outputs:
            pubkeys = [w.pubkey for w in self.account.wallets]
            if o.pubkey in pubkeys:
                outputs.append(o)
                amount += o.amount
        comment = tx[1].comment
        pubkey = tx[1].issuers[0]
        try:
            #sender = Person.lookup(pubkey, self.community).name
            sender = Person.lookup(pubkey, self.community)
        except PersonNotFoundError:
            #sender = "pub:{0}".format(pubkey[:5])
            sender = pubkey

        date_ts = self.community.get_block(tx[0]).time
        date = QDateTime.fromTime_t(date_ts)

        amount_ref = self.account.units_to_ref(amount, self.community)
        ref_name = self.account.ref_name(self.community.short_currency)

        return (date.date(), sender, "", "{0:.2f} {1}".format(amount_ref, ref_name),
                comment)

    def data_sent(self, tx):
        amount = 0
        outputs = []
        for o in tx[1].outputs:
            pubkeys = [w.pubkey for w in self.account.wallets]
            if o.pubkey not in pubkeys:
                outputs.append(o)
                amount += o.amount

        comment = tx[1].comment
        pubkey = outputs[0].pubkey
        try:
            #receiver = Person.lookup(pubkey, self.community).name
            receiver = Person.lookup(pubkey, self.community)
        except PersonNotFoundError:
            #receiver = "pub:{0}".format(pubkey[:5])
            receiver = pubkey

        date_ts = self.community.get_block(tx[0]).time
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

        if role == Qt.DisplayRole:
            if self.transactions[row] in self.account.transactions_sent(self.community) \
                or self.transactions[row] in self.account.transactions_awaiting(self.community):
                return self.data_sent(self.transactions[row])[col]

            if self.transactions[row] in self.account.transactions_received(self.community):
                return self.data_received(self.transactions[row])[col]

        if role == Qt.FontRole:
            font = QFont()
            if self.transactions[row] in self.account.transactions_awaiting(self.community):
                font.setItalic(True)
            else:
                font.setItalic(False)
            return font

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
