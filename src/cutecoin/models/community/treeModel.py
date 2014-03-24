'''
Created on 5 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from cutecoin.models.node.itemModel import MainNodeItem, NodeItem
from cutecoin.models.community.itemModel import CommunityItemModel
import logging


class CommunityTreeModel(QAbstractItemModel):

    '''
    A Qt abstract item model to display nodes of a community
    '''

    def __init__(self, community):
        '''
        Constructor
        '''
        super(CommunityTreeModel, self).__init__(None)
        self.community = community
        self.root_item = CommunityItemModel(self.community)
        self.refresh_tree_nodes()

    def columnCount(self, parent):
        return 3

    def data(self, index, role):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole and index.column() == 0:
            return item.data(0)
        elif role == Qt.CheckStateRole and index.column() == 1:
            return Qt.Checked if item.trust else Qt.Unchecked
        elif role == Qt.CheckStateRole and index.column() == 2:
            return Qt.Checked if item.hoster else Qt.Unchecked

        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        if index.column() == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
            return self.root_item.data(0) + " nodes"
        elif orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 1:
            return "Trust"
        elif orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 2:
            return "Hoster"
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
            return False

        if role == Qt.EditRole:
            return False
        if role == Qt.CheckStateRole:
            item = index.internalPointer()
            if index.column() == 1:
                item.trust = value
            elif index.column() == 2:
                item.host = value
            self.data_changed.emit(index, index)
            return True

    def refresh_tree_nodes(self):
        logging.debug("root : " + self.root_item.data(0))
        for main_node in self.community.nodes:
            main_node_item = MainNodeItem(main_node, self.root_item)
            logging.debug(
                "mainNode : " +
                main_node.getText() +
                " / " +
                main_node_item.data(0))
            self.root_item.appendChild(main_node_item)
            for node in main_node.downstream_peers():
                node_item = NodeItem(node, main_node_item)
                logging.debug(
                    "\t node : " +
                    node.getText() +
                    " / " +
                    node_item.data(0))
                main_node_item.appendChild(node_item)
