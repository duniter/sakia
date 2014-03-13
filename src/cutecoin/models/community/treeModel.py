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
        self.rootItem = CommunityItemModel(self.community)
        self.refreshTreeNodes()

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
            return Qt.ItemIsEnabled  | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 0:
            return self.rootItem.data(0) + " nodes"
        elif orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 1:
            return "Trust"
        elif orientation == Qt.Horizontal and role == Qt.DisplayRole and section == 2:
            return "Hoster"
        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if parent.column() > 0:
            return 0

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

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
            self.dataChanged.emit(index, index)
            return True

    def refreshTreeNodes(self):
        logging.debug("root : " + self.rootItem.data(0))
        for mainNode in self.community.nodes:
            mainNodeItem = MainNodeItem(mainNode, self.rootItem)
            logging.debug("mainNode : " + mainNode.getText() + " / " + mainNodeItem.data(0))
            self.rootItem.appendChild(mainNodeItem)
            for node in mainNode.downstreamPeers():
                nodeItem = NodeItem(node, mainNodeItem)
                logging.debug("\t node : " + node.getText()+ " / " + nodeItem.data(0))
                mainNodeItem.appendChild(nodeItem)

