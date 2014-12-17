'''
Created on 5 févr. 2014

@author: inso
'''

from cutecoin.core.person import Person
from PyQt5.QtCore import QAbstractListModel, Qt


class MembersListModel(QAbstractListModel):

    '''
    A Qt abstract item model to display communities in a tree
    '''

    def __init__(self, community, parent=None):
        '''
        Constructor
        '''
        super(MembersListModel, self).__init__(parent)
        pubkeys = community.members_pubkeys()
        self.members = []
        for p in pubkeys:
            self.members.append(Person.lookup(p, community))

    def rowCount(self, parent):
        return len(self.members)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            row = index.row()
            value = self.members[row].name
            return value

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
