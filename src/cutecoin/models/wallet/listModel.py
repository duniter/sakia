'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt


class WalletListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, wallet, parent=None):
        '''
        Constructor
        '''
        super(WalletListModel, self).__init__(parent)
        self.coins = wallet.coins

    def rowCount(self, parent):
        return len(self.coins)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            value = str(self.coins[row].value())
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
