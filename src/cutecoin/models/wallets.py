'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt


class WalletsListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, account, parent=None):
        '''
        Constructor
        '''
        super(WalletsListModel, self).__init__(parent)
        self.wallets = account.wallets
        self.communities = account.communities

    def rowCount(self, parent):
        return len(self.wallets) * len(self.communities)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            index_community = row % len(self.communities)
            index_wallet = int(row / len(self.communities))
            value = self.wallets[index_wallet].get_text(self.communities[index_community])
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
