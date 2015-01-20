'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.person import Person
from ..tools.exceptions import PersonNotFoundError
from PyQt5.QtCore import QAbstractListModel, Qt
from PyQt5.QtGui import QFont


class SentListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, account, community, parent=None):
        '''
        Constructor
        '''
        super(SentListModel, self).__init__(parent)
        self.account = account
        self.community = community

    def rowCount(self, parent):
        return len(self.account.transactions_sent(self.community)) \
            + len(self.account.transactions_awaiting(self.community))

    def data(self, index, role):
        row = index.row()
        if role == Qt.DisplayRole:
            transactions = []
            if row < len(self.account.transactions_sent(self.community)):
                transactions = self.account.transactions_sent(self.community)
            else:
                transactions = self.account.transactions_awaiting(self.community)
                row = row - len(self.account.transactions_sent(self.community))
            amount = 0
            outputs = []
            for o in transactions[row].outputs:
                pubkeys = [w.pubkey for w in self.account.wallets]
                if o.pubkey not in pubkeys:
                    outputs.append(o)
                    amount += o.amount
            try:
                receiver = Person.lookup(outputs[0].pubkey, self.community)
                value = "{0} to {1}".format(amount, receiver.name)
            except PersonNotFoundError:
                value = "{0} to {1}".format(amount, outputs[0].pubkey)
            return value

        if role == Qt.FontRole:
            font = QFont()
            if row < len(self.account.transactions_sent(self.community)):
                font.setItalic(False)
            else:
                font.setItalic(True)
            return font

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
