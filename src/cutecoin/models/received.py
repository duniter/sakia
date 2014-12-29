'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.person import Person
from PyQt5.QtCore import QAbstractListModel, Qt


class ReceivedListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, account, community, parent=None):
        '''
        Constructor
        '''
        super(ReceivedListModel, self).__init__(parent)
        self.account = account
        self.community = community

    def rowCount(self, parent):
        return len(self.account.transactions_received(self.community))

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            transactions = self.account.transactions_received(self.community)
            amount = 0
            for o in transactions[row].outputs:
                pubkeys = [w.pubkey for w in self.account.wallets]
                if o.pubkey in pubkeys:
                    amount += o.amount
            pubkey = transactions[row].issuers[0]
            sender = Person.lookup(pubkey, self.community)
            value = "{0} from {1}".format(amount, sender.name)
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
