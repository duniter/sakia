'''
Created on 5 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt


class CommunitiesListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, account, parent=None):
        '''
        Constructor
        '''
        super(CommunitiesListModel, self).__init__(parent)
        self.communities = account.communities

    def rowCount(self, parent):
        return len(self.communities)

    def data(self, index, role):

        if role == Qt.DisplayRole:
            row = index.row()
            value = self.communities[row].name
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
