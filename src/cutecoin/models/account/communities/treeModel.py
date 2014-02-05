'''
Created on 5 févr. 2014

@author: inso
'''

from PyQt5.QtCore import QAbstractItemModel, Qt, QModelIndex
from cutecoin.models.node.itemModel import NodeTreeItem
from cutecoin.models.account.communities.itemModel import CommunitiesItemModel
from cutecoin.models.community.itemModel import CommunityItemModel
from cutecoin.models.node.itemModel import MainNodeTreeItem

class CommunitiesTreeModel(QAbstractItemModel):
    '''
    A Qt abstract item model to display communities in a tree
    '''
    def __init__(self, account):
        '''
        Constructor
        '''
        super(CommunitiesTreeModel, self).__init__(None)
        self.communities = account.communities
        self.rootItem = CommunitiesItemModel(account)
        self.refreshTreeNodes()

    def columnCount(self, parent):
        return 1

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole:
            return None

        item = index.internalPointer()

        return item.data

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags

        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return "Communities nodes"

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
        for community in self.communities.communitiesList:
            communityItem = CommunityItemModel(community, self)
            self.rootItem.appendChild(communityItem)
            for mainNode in community.knownNodes:
                mainNodeItem = MainNodeTreeItem(mainNode, communityItem)
                communityItem.appendChild(mainNodeItem)
                for node in mainNode.downstreamPeers():
                    nodeItem = NodeTreeItem(node, mainNodeItem)
                    mainNodeItem.appendChild(nodeItem)




