'''
Created on 5 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy.documents.peer import BMAEndpoint, Peer
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from requests.exceptions import Timeout
import logging


class RootItem(object):

    def __init__(self, name):
        self.name = name
        self.node_items = []

    def appendChild(self, item):
        self.node_items.append(item)

    def child(self, row):
        return self.node_items[row]

    def childCount(self):
        return len(self.node_items)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.name
        except IndexError:
            return None

    def parent(self):
        return None

    def row(self):
        return 0


class NodeItem(object):

    def __init__(self, node, root_item):
        e = node.endpoint
        if e.server:
            self.address = "{0}:{1}".format(e.server, e.port)
        elif e.ipv4:
            self.address = "{0}:{1}".format(e.ipv4, e.port)
        elif e.ipv6:
            self.address = "{0}:{1}".format(e.ipv6, e.port)
        else:
            self.address = "{0}".format(node.pubkey)

        self.root_item = root_item
        self.node_items = []

    def appendChild(self, node_item):
        self.node_items.append(node_item)

    def child(self, row):
        return self.node_items[row]

    def childCount(self):
        return len(self.node_items)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.address
        except IndexError:
            return None

    def parent(self):
        return self.root_item

    def row(self):
        if self.root_item:
            return self.root_item.node_items.index(self)
        return 0


class PeeringTreeModel(QAbstractItemModel):

    '''
    A Qt abstract item model to display nodes of a community
    '''

    def __init__(self, community):
        '''
        Constructor
        '''
        super().__init__(None)
        self.nodes = community.nodes
        self.root_item = RootItem(community.currency)
        self.refresh_tree()

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole and index.column() == 0:
            return item.data(0)

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal \
        and role == Qt.DisplayRole and section == 0:
            return self.root_item.data(0) + " nodes"
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = index.internalPointer()
        parent_item = child_item.parent()

        if parent_item == self.root_item:
            return QModelIndex()

        return self.createIndex(parent_item.row(), 0, parent_item)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parent_item = self.root_item
        else:
            parent_item = parent.internalPointer()

        return parent_item.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        if index.column() == 0:
            return True

    def refresh_tree(self):
        logging.debug("root : " + self.root_item.data(0))
        for node in self.nodes:
            node_item = NodeItem(node, self.root_item)
            self.root_item.appendChild(node_item)
