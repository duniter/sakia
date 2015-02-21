'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..core.transfer import Transfer, Received
from ..core.person import Person
from ..tools.exceptions import PersonNotFoundError
from ucoinpy.documents.peer import BMAEndpoint
from ucoinpy.api import bma
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
                        QDateTime
from PyQt5.QtGui import QFont, QColor


class NetworkFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.community = None

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None)

    def setSourceModel(self, sourceModel):
        self.community = sourceModel.community
        super().setSourceModel(sourceModel)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        return (left_data < right_data)

    def data(self, index, role):
        source_index = self.mapToSource(index)
        source_data = self.sourceModel().data(source_index, role)
        return source_data


class NetworkTableModel(QAbstractTableModel):

    '''
    A Qt abstract item model to display
    '''

    def __init__(self, community, parent=None):
        '''
        Constructor
        '''
        super().__init__(parent)
        self.community = community
        self.column_types = (
            'address',
            'port'
        )

    @property
    def peers(self):
        return self.community.peers

    def rowCount(self, parent):
        return len(self.peers)

    def columnCount(self, parent):
        return len(self.column_types)

    def headerData(self, section, orientation, role):
        return self.column_types[section]

    def data_peer(self, peer):
        e = next((e for e in peer.endpoints if type(e) is BMAEndpoint))
        informations = bma.network.peering.Peers(e.conn_handler()).get()
        if e.server:
            address = e.server
        elif e.ipv4:
            address = e.port

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        peer = self.peers[row]
        if role == Qt.DisplayRole:
            return self.data_peer(peer)[col]

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

