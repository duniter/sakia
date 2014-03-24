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

    def rowCount(self, parent):
        return len(self.wallets.wallets_list)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            value = self.wallets.wallets_list[row].getText()
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
