'''
Created on 5 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractListModel, Qt

class IssuancesListModel(QAbstractListModel):
    '''
    A Qt abstract item model to display communities in a tree
    '''
    def __init__(self, community, parent=None):
        '''
        Constructor
        '''
        super(IssuancesListModel, self).__init__(parent)
        #TODO: Manage issuances
        self.issuances = []


    def rowCount(self ,parent):
        return len(self.issuanes)

    def data(self,index,role):

        if role == Qt.DisplayRole:
            row=index.row()
            value = self.issuances[row]
            return value

    def flags(self,index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
