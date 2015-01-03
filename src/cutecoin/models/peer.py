'''
Created on 5 févr. 2014

@author: inso
'''

import logging
from ucoinpy.documents.peer import BMAEndpoint, Peer


class RootItem(object):

    def __init__(self, name):
        self.name = name
        self.main_peer_items = []

    def appendChild(self, item):
        self.main_peer_items.append(item)

    def child(self, row):
        return self.main_peer_items[row]

    def childCount(self):
        return len(self.main_peer_items)

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
        e = next((e for e in main_peer.endpoints if type(e) is BMAEndpoint))
        if e.server:
            self.main_peer_text = "{0}:{1}".format(e.server, e.port)
        elif e.ipv4:
            self.main_peer_text = "{0}:{1}".format(e.ipv4, e.port)
        elif e.ipv6:
            self.main_peer_text = "{0}:{1}".format(e.ipv6, e.port)
        else:
            self.main_peer_text = "{0}".format(main_peer.pubkey)

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
