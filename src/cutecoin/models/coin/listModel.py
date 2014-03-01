'''
Created on 8 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt

class CoinsListModel(QAbstractListModel):
    '''
    A Qt abstract item model to display communities in a tree
    '''
    def __init__(self, coins, parent=None):
        '''
        Constructor
        '''
        super(CoinsListModel, self).__init__(parent)
        self.coins = coins

    def rowCount(self ,parent):
        return len(self.coins)

    def data(self,index,role):
        if role == Qt.DisplayRole:
            row=index.row()
            value = str(self.coins[row].value())
            return value

    def flags(self,index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

    def toList(self):
        coinsList = []
        for c in self.coins:
            coinsList.append(c.getId())
        return coinsList