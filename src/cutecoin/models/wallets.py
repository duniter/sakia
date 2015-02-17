'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractTableModel, Qt
import logging


class WalletsTableModel(QAbstractTableModel):

    '''
    A Qt list model to display wallets and edit their names
    '''

    def __init__(self, account, community, parent=None):
        '''
        Constructor
        '''
        super().__init__(parent)
        self.account = account
        self.community = community
        self.columns_types = ('name', 'pubkey', 'amount')

    @property
    def wallets(self):
        return self.account.wallets

    def rowCount(self, parent):
        return len(self.wallets)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            return self.columns_types[section]

    def wallet_data(self, row):
        name = self.wallets[row].name
        amount = self.wallets[row].value(self.community)
        pubkey = self.wallets[row].pubkey

        return (name, pubkey, amount)

    def data(self, index, role):
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return self.wallet_data(row)[col]

#     def setData(self, index, value, role):
#         if role == Qt.EditRole:
#             row = index.row()
#             self.wallets[row].name = value
#             self.dataChanged.emit(index, index)
#             return True
#         return False

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
