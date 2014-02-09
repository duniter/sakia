'''
Created on 5 févr. 2014

@author: inso
'''

import ucoinpy as ucoin
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
        fingerprints = community.members()
        self.members = []
        '''for f in fingerprints:
            keys = community.ucoinRequest(lambda : ucoin.pks.Lookup().get)
            if len(keys) > 0:
                self.members.append(keys[0]['key']['name'])
        '''

    def rowCount(self ,parent):
        return len(self.members)

    def data(self,index,role):

        if role == Qt.DisplayRole:
            row=index.row()
            value = self.members[row]
            return value

    def flags(self,index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
