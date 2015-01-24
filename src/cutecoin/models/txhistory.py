'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.person import Person
from ..tools.exceptions import PersonNotFoundError
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt5.QtGui import QFont
from operator import itemgetter
import datetime


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

    def rowCount(self, parent):
        transactions = self.account.transactions_sent(self.community) + \
         self.account.transactions_awaiting(self.community) + \
         self.account.transactions_received(self.community)
        return len(transactions)

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
            if o.pubkey not in pubkeys:
                outputs.append(o)
                amount += o.amount
        comment = tx[1].comment
        pubkey = tx[1].issuers[0]
        try:
            sender = Person.lookup(pubkey, self.community).name
        except PersonNotFoundError:
            sender = pubkey

        date_ts = self.community.get_block(tx[0]).mediantime
        date = datetime.datetime.fromtimestamp(date_ts).strftime('%Y-%m-%d %H:%M:%S')

        return (date, sender, "", "{0}".format(amount), comment)

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
            receiver = Person.lookup(pubkey, self.community).name
        except PersonNotFoundError:
            receiver = pubkey
        date_ts = self.community.get_block(tx[0]).mediantime
        date = datetime.datetime.fromtimestamp(date_ts).strftime('%Y-%m-%d %H:%M:%S')

        return (date, receiver, "-{0}".format(amount), "", comment)

    def data(self, index, role):
        row = index.row()
        col = index.column()
        transactions = self.account.transactions_sent(self.community) + \
         self.account.transactions_awaiting(self.community) + \
         self.account.transactions_received(self.community)
        transactions = sorted(transactions, reverse=True, key=itemgetter(0))

        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            if transactions[row] in self.account.transactions_sent(self.community) \
                or transactions[row] in self.account.transactions_awaiting(self.community):
                return self.data_sent(transactions[row])[col]

            if transactions[row] in self.account.transactions_received(self.community):
                return self.data_received(transactions[row])[col]

        if role == Qt.FontRole:
            font = QFont()
            if transactions[row] in self.account.transactions_awaiting(self.community):
                font.setItalic(True)
            else:
                font.setItalic(False)
            return font

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
