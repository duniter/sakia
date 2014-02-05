'''
Created on 5 févr. 2014

@author: inso
'''


class NodeItem(object):
    def __init__(self, node, mainNodeItem=None):
        self.mainNodeItem = mainNodeItem
        self.nodeText = node.getText()

    def appendChild(self, item):
        pass

    def child(self, row):
        return None

    def childCount(self):
        return 0

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.nodeText
        except IndexError:
            return None

    def parent(self):
        return self.mainNodeItem

    def row(self):
        if self.mainNodeItem:
            return self.mainNodeItem.nodeItems.index(self)

        return 0

class MainNodeItem(object):
    def __init__(self, mainNode, communityItem=None):
        self.communityItem = communityItem
        self.mainNodeText = mainNode.getText()
        self.nodeItems = []

    def appendChild(self, nodeItem):
        self.nodeItems.append(nodeItem)

    def child(self, row):
        return self.nodeItems[row]

    def childCount(self):
        return len(self.nodeItems)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.mainNodeText
        except IndexError:
            return None

    def parent(self):
        return self.communityItem

    def row(self):
        if self.communityItem:
            return self.communityItem.mainNodeItems.index(self)

        return 0