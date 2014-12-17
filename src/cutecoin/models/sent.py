'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtCore import QAbstractListModel, Qt


class SentListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, account, parent=None):
        '''
        Constructor
        '''
        super(SentListModel, self).__init__(parent)
        self.transactions = account.transactions_sent()

    def rowCount(self, parent):
        return len(self.transactions)

    def data(self, index, role):

        if role == Qt.DisplayRole:
            row = index.row()
            value = self.transactions[row].get_sender_text()
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
