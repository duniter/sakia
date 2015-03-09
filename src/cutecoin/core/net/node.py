'''
Created on 21 févr. 2015

@author: inso
'''

from ucoinpy.documents.peer import Peer, BMAEndpoint, Endpoint
from ucoinpy.api import bma
from ucoinpy.api.bma import ConnectionHandler
from requests.exceptions import RequestException
from ...tools.exceptions import InvalidNodeCurrency
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

    def __init__(self, currency, endpoints, pubkey, block, state):
        '''
        Constructor
        '''
        super().__init__()
        self._endpoints = endpoints
        self._pubkey = pubkey
        self._block = block
        self._state = state
        self._neighbours = []
        self._currency = currency

    @classmethod
    def from_address(cls, currency, address, port):
        peer_data = bma.network.Peering(ConnectionHandler(address, port)).get()

        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                  peer_data['signature']))

        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer.currency, peer.endpoints, peer.pubkey, 0, Node.ONLINE, 0)
        node.refresh_state()
        return node

    @classmethod
    def from_peer(cls, currency, peer):
        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer.currency, peer.endpoints, "", 0, Node.ONLINE)
        node.refresh_state()
        return node

    @classmethod
    def from_json(cls, currency, data):
        endpoints = []
        for endpoint_data in data['endpoints']:
            endpoints.append(Endpoint.from_inline(endpoint_data))

        currency = data['currency']

        node = cls(currency, endpoints, "", 0, Node.ONLINE)
        node.refresh_state()
        return node

    def jsonify(self):
        data = {'pubkey': self._pubkey,
                'currency': self._currency}
        endpoints = []
        for e in self._endpoints:
            endpoints.append(e.inline())
        data['endpoints'] = endpoints
        return data

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

    @property
    def currency(self):
        return self._currency

    @property
    def neighbours(self):
        return self._neighbours

    def check_sync(self, block):
        if self._block < block:
            self._state = Node.DESYNCED
        else:
            self._state = Node.ONLINE

    def refresh_state(self):
        emit_change = False
        try:
            informations = bma.network.Peering(self.endpoint.conn_handler()).get()
            block = bma.blockchain.Current(self.endpoint.conn_handler()).get()
            peers_data = bma.network.peering.Peers(self.endpoint.conn_handler()).get()
            neighbours = []
            for p in peers_data:
                peer = Peer.from_signed_raw("{0}{1}\n".format(p['value']['raw'],
                                                            p['value']['signature']))
                neighbours.append(peer.endpoints)

            block_number = block["number"]
            node_pubkey = informations["pubkey"]
            node_currency = informations["currency"]
        except ValueError as e:
            if '404' in e:
                block_number = 0
        except RequestException:
            self._state = Node.OFFLINE
            emit_change = True

        # If not is offline, do not refresh last data
        if self._state != Node.OFFLINE:
            # If not changed its currency, consider it corrupted
            if node_currency != self._currency:
                self.state = Node.CORRUPTED
                emit_change = True
            else:
                if block_number != self._block:
                    self._block = block_number
                    emit_change = True

                if node_pubkey != self._pubkey:
                    self._pubkey = node_pubkey
                    emit_change = True

                logging.debug(neighbours)
                new_inlines = [e.inline() for n in neighbours for e in n]
                last_inlines = [e.inline() for n in self._neighbours for e in n]

                hash_new_neighbours = hash(tuple(frozenset(sorted(new_inlines))))
                hash_last_neighbours = hash(tuple(frozenset(sorted(last_inlines))))
                if hash_new_neighbours != hash_last_neighbours:
                    self._neighbours = neighbours
                    emit_change = True

        if emit_change:
            self.changed.emit()

    def peering_traversal(self, found_nodes,
                          traversed_pubkeys, interval):
        logging.debug("Read {0} peering".format(self.pubkey))
        traversed_pubkeys.append(self.pubkey)
        self.refresh_state()

        if self.pubkey not in [n.pubkey for n in found_nodes]:
            # if node is corrupted remove it
            if self._state != Node.CORRUPTED:
                found_nodes.append(self)
        try:
            logging.debug(self.neighbours)
            for n in self.neighbours:
                e = next(e for e in n if type(e) is BMAEndpoint)
                peering = bma.network.Peering(e.conn_handler()).get()
                peer = Peer.from_signed_raw("{0}{1}\n".format(peering['raw'],
                                                            peering['signature']))
                node = Node.from_peer(self._currency, peer)
                logging.debug(traversed_pubkeys)
                logging.debug("Traversing : next to read : {0} : {1}".format(node.pubkey,
                              (node.pubkey not in traversed_pubkeys)))
                if node.pubkey not in traversed_pubkeys:
                    node.peering_traversal(found_nodes,
                                        traversed_pubkeys, interval)
                    time.sleep(interval)
        except RequestException as e:
            self._state = Node.OFFLINE
