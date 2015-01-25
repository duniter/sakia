'''
Created on 5 févr. 2014

@author: inso
'''

from ucoinpy.api import bma
from ucoinpy.documents.peer import BMAEndpoint, Peer
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, Qt
from .peer import PeerItem, RootItem
from requests.exceptions import Timeout
import logging


class PeeringTreeModel(QAbstractItemModel):

    '''
    A Qt abstract item model to display nodes of a community
    '''

    def __init__(self, community):
        '''
        Constructor
        '''
        super().__init__(None)
        self.peers = community.peering()
        self.root_item = RootItem(community.currency)
        self.refresh_tree()

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
        if orientation == Qt.Horizontal \
        and role == Qt.DisplayRole and section == 0:
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

    def refresh_tree(self):
        logging.debug("root : " + self.root_item.data(0))
        for peer in self.peers:
            logging.debug("Browser peers")
            peer_item = PeerItem(peer, self.root_item)
            self.root_item.appendChild(peer_item)
            try:
                e = next((e for e in peer.endpoints if type(e) is BMAEndpoint))
                peers = bma.network.peering.Peers(e.conn_handler()).get()
                try:
                    for peer_data in peers:
                        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['value']['raw'],
                                                                    peer_data['value']['signature']))
                        child_node_item = PeerItem(peer, peer_item)
                        peer_item.appendChild(child_node_item)
                except Timeout:
                    continue

            except StopIteration as e:
                continue
