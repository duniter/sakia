'''
Created on 21 févr. 2015

@author: inso
'''

from ucoinpy.documents.peer import Peer, BMAEndpoint, Endpoint
from ucoinpy.api import bma
from requests.exceptions import RequestException
from ...core.person import Person
from ...tools.exceptions import PersonNotFoundError
import logging
import time

from PyQt5.QtCore import QObject, pyqtSignal


class Node(QObject):
    '''
    classdocs
    '''

    ONLINE = 1
    OFFLINE = 2
    DESYNCED = 3
    CORRUPTED = 4

    changed = pyqtSignal()

    def __init__(self, endpoints, pubkey, block, state):
        '''
        Constructor
        '''
        super().__init__()
        self._endpoints = endpoints
        self._pubkey = pubkey
        self._block = block
        self._state = state

    @classmethod
    def from_peer(cls, currency, peer):
        node = cls(peer.endpoints, "", 0, Node.ONLINE)
        node.refresh_state(currency)
        return node

    @classmethod
    def from_json(cls, currency, data):
        endpoints = []
        for endpoint_data in data['endpoints']:
            endpoints.append(Endpoint.from_inline(endpoint_data))

        node = cls(endpoints, "", 0, Node.ONLINE)
        node.refresh_state(currency)
        return node

    @property
    def pubkey(self):
        return self._pubkey

    @property
    def endpoint(self):
        return next((e for e in self._endpoints if type(e) is BMAEndpoint))

    @property
    def block(self):
        return self._block

    @property
    def state(self):
        return self._state

    def check_sync(self, currency, block):
        if self._block < block:
            self._state = Node.DESYNCED
        else:
            self._state = Node.ONLINE

    def refresh_state(self, currency):
        try:
            informations = bma.network.Peering(self.endpoint.conn_handler()).get()
            block = bma.blockchain.Current(self.endpoint.conn_handler()).get()
            block_number = block["number"]
            node_pubkey = informations["pubkey"]
            node_currency = informations["currency"]
        except ValueError as e:
            if '404' in e:
                block_number = 0
        except RequestException:
            self._state = Node.OFFLINE

        if node_currency != currency:
            self.state = Node.CORRUPTED

        self._block = block_number
        self._pubkey = node_pubkey

    def peering_traversal(self, currency, found_nodes, traversed_pubkeys, interval):
        logging.debug("Read {0} peering".format(self.pubkey))
        traversed_pubkeys.append(self.pubkey)
        self.refresh_state(currency)
        if self.pubkey not in [n.pubkey for n in found_nodes]:
            found_nodes.append(self)

        try:
            next_peers = bma.network.peering.Peers(self.endpoint.conn_handler()).get()
            for p in next_peers:
                next_peer = Peer.from_signed_raw("{0}{1}\n".format(p['value']['raw'],
                                                            p['value']['signature']))
                logging.debug(traversed_pubkeys)
                logging.debug("Traversing : next to read : {0} : {1}".format(next_peer.pubkey,
                              (next_peer.pubkey not in traversed_pubkeys)))
                next_node = Node.from_peer(next_peer)
                if next_node.pubkey not in traversed_pubkeys:
                    next_node.peering_traversal(currency, found_nodes, traversed_pubkeys)
                    time.sleep(interval)
        except RequestException as e:
            self._state = Node.OFFLINE
