'''
Created on 21 févr. 2015

@author: inso
'''

from ucoinpy.documents.peer import Peer, BMAEndpoint, Endpoint
from ucoinpy.api import bma
from ucoinpy.api.bma import ConnectionHandler
from requests.exceptions import RequestException
from ...tools.exceptions import InvalidNodeCurrency, PersonNotFoundError
from ..person import Person
import logging
import time

from PyQt5.QtCore import QObject, pyqtSignal


class Node(QObject):
    '''
    A node is a peer seend from the client point of view.
    This node can have multiple states :
    - ONLINE : The node is available for requests
    - OFFLINE: The node is disconnected
    - DESYNCED : The node is online but is desynced from the network
    - CORRUPTED : The node is corrupted, some weird behaviour is going on
    '''

    ONLINE = 1
    OFFLINE = 2
    DESYNCED = 3
    CORRUPTED = 4

    changed = pyqtSignal()

    def __init__(self, currency, endpoints, uid, pubkey, block,
                 state, last_change):
        '''
        Constructor
        '''
        super().__init__()
        self._endpoints = endpoints
        self._uid = uid
        self._pubkey = pubkey
        self._block = block
        self._state = state
        self._neighbours = []
        self._currency = currency
        self._last_change = last_change

    @classmethod
    def from_address(cls, currency, address, port):
        '''
        Factory method to get a node from a given address

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param str address: The node address
        :param int port: The node port
        '''
        peer_data = bma.network.Peering(ConnectionHandler(address, port)).get()

        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                  peer_data['signature']))

        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer.currency, peer.endpoints, "", peer.pubkey, 0,
                   Node.ONLINE, time.time())
        node.refresh_state()
        return node

    @classmethod
    def from_peer(cls, currency, peer):
        '''
        Factory method to get a node from a peer document.

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param peer: The peer document
        '''
        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer.currency, peer.endpoints, "", "", 0,
                   Node.ONLINE, time.time())
        node.refresh_state()
        return node

    @classmethod
    def from_json(cls, currency, data):
        endpoints = []
        uid = ""
        pubkey = ""
        last_change = time.time()
        state = Node.ONLINE
        logging.debug(data)
        for endpoint_data in data['endpoints']:
            endpoints.append(Endpoint.from_inline(endpoint_data))

        if currency in data:
            currency = data['currency']

        if 'uid' in data:
            uid = data['uid']

        if 'pubkey' in data:
            pubkey = data['pubkey']

        if 'last_change' in data:
            last_change = data['last_change']

        if 'state' in data:
            state = data['state']
        else:
            logging.debug("Error : no state in node")

        node = cls(currency, endpoints, uid, pubkey, 0,
                   state, last_change)
        node.refresh_state()
        return node

    def jsonify(self):
        data = {'pubkey': self._pubkey,
                'uid': self._uid,
                'currency': self._currency,
                'state': self._state,
                'last_change': self._last_change}
        endpoints = []
        for e in self._endpoints:
            endpoints.append(e.inline())
        data['endpoints'] = endpoints
        return data

    @property
    def pubkey(self):
        return self._pubkey

    @property
    def endpoint(self) -> BMAEndpoint:
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

    @property
    def uid(self):
        return self._uid

    @property
    def last_change(self):
        return self._last_change

    @last_change.setter
    def last_change(self, val):
        logging.debug("{:} | Changed state : {:}".format(self.pubkey[:5],
                                                         val))
        self._last_change = val

    def _change_state(self, new_state):
        logging.debug("{:} | Last state : {:} / new state : {:}".format(self.pubkey[:5],
                                                                        self.state, new_state))
        if self.state != new_state:
            self.last_change = time.time()
        self._state = new_state

    def check_sync(self, block):
        logging.debug("Check sync")
        if self._block < block:
            self._change_state(Node.DESYNCED)
        else:
            self._change_state(Node.ONLINE)

    def _request_uid(self):
        uid = ""
        try:
            data = bma.wot.Lookup(self.endpoint.conn_handler(), self.pubkey).get()
            timestamp = 0
            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    uids = result['uids']
                    for uid in uids:
                        if uid["meta"]["timestamp"] > timestamp:
                            timestamp = uid["meta"]["timestamp"]
                            uid = uid["uid"]
        except ValueError as e:
            if '404' in str(e):
                logging.debug("Error : node uid not found : {0}".format(self.pubkey))
                uid = ""
        return uid

    def refresh_state(self):
        logging.debug("Refresh state")
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

            #If the nodes goes back online...
            if self.state in (Node.OFFLINE, Node.CORRUPTED):
                self._change_state(Node.ONLINE)
                emit_change = True
        except ValueError as e:
            if '404' in e:
                block_number = 0
        except RequestException:
            self._change_state(Node.OFFLINE)
            emit_change = True

        # If not is offline, do not refresh last data
        if self.state != Node.OFFLINE:
            # If not changed its currency, consider it corrupted
            if node_currency != self._currency:
                self._change_state(Node.CORRUPTED)
                emit_change = True
            else:
                node_uid = self._request_uid()

                if block_number != self._block:
                    self._block = block_number
                    emit_change = True

                if node_pubkey != self._pubkey:
                    self._pubkey = node_pubkey
                    emit_change = True

                if node_uid != self._uid:
                    self._uid = node_uid
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
                          traversed_pubkeys, interval,
                          continue_crawling):
        logging.debug("Read {0} peering".format(self.pubkey))
        traversed_pubkeys.append(self.pubkey)
        self.refresh_state()

        if self.pubkey not in [n.pubkey for n in found_nodes]:
            # if node is corrupted remove it
            if self.state != Node.CORRUPTED:
                logging.debug("Found : {0} node".format(self.pubkey))
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
                if node.pubkey not in traversed_pubkeys and continue_crawling():
                    node.peering_traversal(found_nodes,
                                        traversed_pubkeys, interval, continue_crawling)
                    time.sleep(interval)
        except RequestException as e:
            self._change_state(Node.OFFLINE)

    def __str__(self):
        return ','.join([str(self.pubkey), str(self.endpoint.server), str(self.endpoint.port), str(self.block),
                         str(self.currency), str(self.state), str(self.neighbours)])
