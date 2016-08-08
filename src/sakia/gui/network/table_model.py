"""
Created on 5 févr. 2014

@author: inso
"""

import logging
import asyncio

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, QDateTime, QLocale
from PyQt5.QtGui import QColor, QFont, QIcon

from sakia.tools.exceptions import NoPeerAvailable
from sakia.tools.decorators import asyncify, once_at_a_time, cancel_once_task
from sakia.core.net.node import Node


class NetworkFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.community = None

    def columnCount(self, parent):
        return self.sourceModel().columnCount(None) - 2

    def change_community(self, community):
        """
        Change current community and returns refresh task
        :param sakia.core.Community community:
        :return: the refresh task
        :rtype: asyncio.Task
        """
        self.community = community
        return self.sourceModel().change_community(community)

    def setSourceModel(self, sourceModel):
        self.community = sourceModel.community
        super().setSourceModel(sourceModel)

    def lessThan(self, left, right):
        """
        Sort table by given column number.
        """
        source_model = self.sourceModel()
        left_data = self.sourceModel().data(left, Qt.DisplayRole)
        right_data = self.sourceModel().data(right, Qt.DisplayRole)
        if left.column() in (source_model.columns_types.index('port'),
                             source_model.columns_types.index('current_block'),
                             source_model.columns_types.index('current_time')):
            left_data = int(left_data) if left_data != '' else 0
            right_data = int(right_data) if right_data != '' else 0

        return left_data < right_data

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        header_names = {
            'address': self.tr('Address'),
            'port': self.tr('Port'),
            'current_block': self.tr('Block'),
            'current_hash': self.tr('Hash'),
            'current_time': self.tr('Time'),
            'uid': self.tr('UID'),
            'is_member': self.tr('Member'),
            'pubkey': self.tr('Pubkey'),
            'software': self.tr('Software'),
            'version': self.tr('Version')
        }
        _type = self.sourceModel().headerData(section, orientation, role)
        return header_names[_type]

    def data(self, index, role):
        source_index = self.mapToSource(index)
        source_model = self.sourceModel()
        if not source_index.isValid():
            return QVariant()
        source_data = source_model.data(source_index, role)

        if role == Qt.DisplayRole:
            if index.column() == source_model.columns_types.index('is_member'):
                value = {True: self.tr('yes'), False: self.tr('no'), None: self.tr('offline')}
                return value[source_data]

            if index.column() == source_model.columns_types.index('pubkey'):
                return source_data[:5]

            if index.column() == source_model.columns_types.index('current_block'):
                if source_data == -1:
                    return ""
                else:
                    return source_data

            if index.column() == source_model.columns_types.index('current_hash') :
                return source_data[:10]

            if index.column() == source_model.columns_types.index('current_time') and source_data:
                return QLocale.toString(
                            QLocale(),
                            QDateTime.fromTime_t(source_data),
                            QLocale.dateTimeFormat(QLocale(), QLocale.ShortFormat)
                        )

        if role == Qt.TextAlignmentRole:
            if source_index.column() == source_model.columns_types.index('address') or source_index.column() == self.sourceModel().columns_types.index('current_block'):
                return Qt.AlignRight | Qt.AlignVCenter
            if source_index.column() == source_model.columns_types.index('is_member'):
                return Qt.AlignCenter

        if role == Qt.FontRole:
            is_root_col = source_model.columns_types.index('is_root')
            index_root_col = source_model.index(source_index.row(), is_root_col)
            if source_model.data(index_root_col, Qt.DisplayRole):
                font = QFont()
                font.setBold(True)
                return font

        return source_data


class NetworkTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display
    """

    def __init__(self, community, parent=None):
        """
        Constructor
        """
        super().__init__(parent)
        self.community = community
        self.columns_types = (
            'address',
            'port',
            'current_block',
            'current_hash',
            'current_time',
            'uid',
            'is_member',
            'pubkey',
            'software',
            'version',
            'is_root',
            'state'
        )
        self.node_colors = {
            Node.ONLINE: QColor('#99ff99'),
            Node.OFFLINE: QColor('#ff9999'),
            Node.DESYNCED: QColor('#ffbd81'),
            Node.CORRUPTED: QColor(Qt.lightGray)
        }
        self.node_icons = {
            Node.ONLINE: ":/icons/synchronized",
            Node.OFFLINE: ":/icons/offline",
            Node.DESYNCED: ":/icons/forked",
            Node.CORRUPTED: ":/icons/corrupted"
        }
        self.node_states = {
            Node.ONLINE: lambda: self.tr('Online'),
            Node.OFFLINE: lambda: self.tr('Offline'),
            Node.DESYNCED: lambda: self.tr('Unsynchronized'),
            Node.CORRUPTED: lambda: self.tr('Corrupted')
        }
        self.nodes_data = []
        self.community.network.nodes_changed.connect(self.refresh_nodes)

    async def data_node(self, node: Node) -> tuple:
        """
        Return node data tuple
        :param ..core.net.node.Node node: Network node
        :return:
        """
        try:
            members_pubkey = await self.community.members_pubkeys()
            is_member = node.pubkey in members_pubkey
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

        is_root = self.community.network.is_root_node(node)
        if node.block:
            number, block_hash, block_time = node.block['number'], node.block['hash'], node.block['medianTime']
        else:
            number, block_hash, block_time = "", "", ""
        return (address, port, number, block_hash, block_time, node.uid,
                is_member, node.pubkey, node.software, node.version, is_root, node.state)

    @once_at_a_time
    @asyncify
    async def refresh_nodes(self):
        self.beginResetModel()
        self.nodes_data = []
        nodes_data = []
        if self.community:
            for node in self.community.network.nodes:
                data = await self.data_node(node)
                nodes_data.append(data)
        self.nodes_data = nodes_data
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.nodes_data)

    def columnCount(self, parent):
        return len(self.columns_types)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return QVariant()

        return self.columns_types[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        node = self.nodes_data[row]
        if role == Qt.DisplayRole:
            return node[col]
        if role == Qt.BackgroundColorRole:
            return self.node_colors[node[self.columns_types.index('state')]]
        if role == Qt.ToolTipRole:
            return self.node_states[node[self.columns_types.index('state')]]()

        if role == Qt.DecorationRole and index.column() == 0:
            return QIcon(self.node_icons[node[self.columns_types.index('state')]])

        return QVariant()

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

