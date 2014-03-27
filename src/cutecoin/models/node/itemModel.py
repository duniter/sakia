'''
Created on 5 févr. 2014

@author: inso
'''


class NodeItem(object):

    def __init__(self, main_node, community_item=None):
        self.community_item = community_item
        self.main_node_text = main_node.getText()
        self.trust = main_node.trust
        self.hoster = main_node.hoster
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
            return self.main_node_text
        except IndexError:
            return None

    def parent(self):
        return self.community_item

    def row(self):
        if self.community_item:
            return self.community_item.main_node_items.index(self)

        return 0
