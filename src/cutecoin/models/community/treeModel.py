'''
Created on 5 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from cutecoin.models.node.itemModel import MainNodeItem, NodeItem
from cutecoin.models.community.itemModel import CommunityItemModel

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
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data(0)

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.rootItem.data(0)

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


    def refreshTreeNodes(self):

        print("root : " + self.rootItem.data(0))
        for mainNode in self.community.knownNodes:
            mainNodeItem = MainNodeItem(mainNode, self.rootItem)
            print("mainNode : " + mainNode.getText() + " / " + mainNodeItem.data(0))
            self.rootItem.appendChild(mainNodeItem)
            for node in mainNode.downstreamPeers():
                nodeItem = NodeItem(node, mainNodeItem)
                print("\t node : " + node.getText()+ " / " + nodeItem.data(0))
                mainNodeItem.appendChild(nodeItem)

