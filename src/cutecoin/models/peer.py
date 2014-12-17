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


class PeerItem(object):

    def __init__(self, main_peer, root_item):
        self.main_peer_text = main_peer.pubkey
        self.root_item = root_item
        self.peer_items = []

    def appendChild(self, node_item):
        self.peer_items.append(node_item)

    def child(self, row):
        return self.peer_items[row]

    def childCount(self):
        return len(self.peer_items)

    def columnCount(self):
        return 1

    def data(self, column):
        try:
            return self.main_peer_text
        except IndexError:
            return None

    def parent(self):
        return self.root_item

    def row(self):
        if self.root_item:
            return self.root_item.main_peer_items.index(self)
        return 0
