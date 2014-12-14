'''
Created on 5 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from cutecoin.models.node.itemModel import NodeItem, RootItem
import logging


class NodesTreeModel(QAbstractItemModel):

    '''
    A Qt abstract item model to display nodes of a community
    '''

    def __init__(self, nodes, community_name):
        '''
        Constructor
        '''
        super(NodesTreeModel, self).__init__(None)
        self.nodes = nodes
        self.root_item = RootItem(community_name)
        self.refresh_tree_nodes()

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
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
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

    def refresh_tree_nodes(self):
        logging.debug("root : " + self.root_item.data(0))
        for node in self.nodes:
            node_item = NodeItem(node, self.root_item)
            logging.debug(
                "mainNode : " +
                node.get_text() +
                " / " +
                node_item.data(0))
            self.root_item.appendChild(node_item)
            for node in node.peers():
                child_node_item = NodeItem(node, node_item)
                logging.debug(
                    "\t node : " +
                    node.get_text() +
                    " / " +
                    child_node_item.data(0))
                node_item.appendChild(child_node_item)
