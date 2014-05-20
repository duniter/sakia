'''
Created on 5 févr. 2014

@author: inso
'''

import logging


class RootItem(object):

    def __init__(self, name):
        self.name = name
        self.main_node_items = []

    def appendChild(self, item):
        self.main_node_items.append(item)

    def child(self, row):
        return self.main_node_items[row]

    def childCount(self):
        return len(self.main_node_items)

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

    def __init__(self, main_node, root_item):
        self.main_node_text = main_node.get_text()
        self.root_item = root_item
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
        return self.root_item

    def row(self):
        if self.root_item:
            return self.root_item.main_node_items.index(self)
        return 0
