'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ..tools.exceptions import NoPeerAvailable
from ..core.net.node import Node
from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel
from PyQt5.QtGui import QColor


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

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        header_names = {
            'address': 'Address',
            'port': 'Port',
            'current_block': 'Block',
            'uid': 'UID',
            'is_member': 'Member',
            'pubkey': 'Pubkey'
        }
        _type = self.sourceModel().headerData(section, orientation, role)
        return header_names[_type]

    def data(self, index, role):
        source_index = self.mapToSource(index)
        if not source_index.isValid():
            return QVariant()
        source_data = self.sourceModel().data(source_index, role)
        if index.column() == self.sourceModel().column_types.index('is_member') \
                and role == Qt.DisplayRole:
            value = {True: 'yes', False: 'no', None: 'offline'}
            return value[source_data]

        if role == Qt.TextAlignmentRole:
            if source_index.column() == self.sourceModel().column_types.index('address') or source_index.column() == self.sourceModel().column_types.index('current_block'):
                return Qt.AlignRight | Qt.AlignVCenter
            if source_index.column() == self.sourceModel().column_types.index('is_member'):
                return Qt.AlignCenter

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
            'port',
            'current_block',
            'uid',
            'is_member',
            'pubkey'
        )
        self.node_colors = {
            Node.ONLINE: QColor('#99ff99'),
            Node.OFFLINE: QColor('#ff9999'),
            Node.DESYNCED: QColor('#ffbd81'),
            Node.CORRUPTED: QColor(Qt.lightGray)
        }
        self.node_states = {
            Node.ONLINE: 'Online',
            Node.OFFLINE: 'Offline',
            Node.DESYNCED: 'Unsynchronized',
            Node.CORRUPTED: 'Corrupted'
        }

    @property
    def nodes(self):
        return self.community.nodes

    def rowCount(self, parent):
        return len(self.nodes)

    def columnCount(self, parent):
        return len(self.column_types)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        return self.column_types[section]

    def data_node(self, node: Node) -> tuple:
        """
        Return node data tuple
        :param ..core.net.node.Node node: Network node
        :return:
        """
        try:
            is_member = node.pubkey in self.community.members_pubkeys()
        except NoPeerAvailable as e:
            logging.error(e)
            is_member = None

        address = ""
        if node.endpoint.server:
            address = node.endpoint.server
        elif node.endpoint.ipv4:
            address = node.endpoint.ipv4
        elif node.endpoint.ipv6:
            address = node.endpoint.ipv6
        port = node.endpoint.port

        return address, port, node.block, node.uid, is_member, node.pubkey

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        node = self.nodes[row]
        if role == Qt.DisplayRole:
            return self.data_node(node)[col]
        if role == Qt.BackgroundColorRole:
            return self.node_colors[node.state]
        if role == Qt.ToolTipRole:
            return self.node_states[node.state]

        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

