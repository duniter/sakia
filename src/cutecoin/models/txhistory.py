'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.person import Person
from ..tools.exceptions import PersonNotFoundError
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant
from PyQt5.QtGui import QFont


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
        self.columns = ('date', 'uid', 'pubkey', 'output', 'input')

    def rowCount(self, parent):
        transactions = self.account.transactions_sent(self.community) + \
         self.account.transactions_awaiting(self.community) + \
         self.account.transactions_received(self.community)
        logging.debug("rowcount: {0}:{1}".format(parent.row(), len(transactions)))
        return len(transactions)

    def columnCount(self, parent):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.columns[section]

    def data_received(self, tx):
        outputs = []
        amount = 0
        for o in tx.outputs:
            pubkeys = [w.pubkey for w in self.account.wallets]
            if o.pubkey not in pubkeys:
                outputs.append(o)
                amount += o.amount

        pubkey = tx.issuers[0]
        sender = ""
        try:
            sender = Person.lookup(pubkey, self.community)
        except PersonNotFoundError:
            sender = ""

        return ("", sender.name, pubkey, "", "{0}".format(amount))

    def data_sent(self, tx):
        amount = 0
        outputs = []
        for o in tx.outputs:
            pubkeys = [w.pubkey for w in self.account.wallets]
            if o.pubkey not in pubkeys:
                outputs.append(o)
                amount += o.amount

        pubkey = outputs[0].pubkey
        receiver = ""
        try:
            receiver = Person.lookup(pubkey, self.community)
        except PersonNotFoundError:
            receiver = ""

        return ("", receiver.name, pubkey, "-{0}".format(amount), "")

    def data(self, index, role):
        row = index.row()
        col = index.column()
        transactions = self.account.transactions_sent(self.community) + \
         self.account.transactions_awaiting(self.community) + \
         self.account.transactions_received(self.community)

        if not index.isValid():
            return QVariant()

        if role == Qt.DisplayRole:
            logging.debug("{0}/{1}".format(row, len(transactions)))
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
