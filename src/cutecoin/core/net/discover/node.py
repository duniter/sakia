'''
Created on 21 févr. 2015

@author: inso
'''

from ucoinpy.documents.peer import Peer, BMAEndpoint, Endpoint
from requests.exceptions import RequestException, ConnectionError
from ....tools.exceptions import InvalidNodeCurrency, PersonNotFoundError
from ...person import Person
from ..api import bma as qtbma
from ..api.bma import ConnectionHandler

import logging
import time
import ctypes
import sys
import json

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest


def some_print():
    logging.debug("Module : ok !")

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
    neighbour_found = pyqtSignal(Peer)

    def __init__(self, network_manager, currency, endpoints, uid, pubkey, block,
                 state, last_change):
        '''
        Constructor
        '''
        super().__init__()
        self.network_manager = network_manager
        self._endpoints = endpoints
        self._uid = uid
        self._pubkey = pubkey
        self.block = block
        self._state = state
        self._neighbours = []
        self._currency = currency
        self._last_change = last_change

    @classmethod
    def from_address(cls, network_manager, currency, address, port):
        '''
        Factory method to get a node from a given address

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param str address: The node address
        :param int port: The node port
        '''
        peer_data = qtbma.network.Peering(ConnectionHandler(network_manager, address, port)).get()

        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                  peer_data['signature']))

        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(network_manager, peer.currency, peer.endpoints,
                   "", peer.pubkey, 0,
                   Node.ONLINE, time.time())
        logging.debug("Node from address : {:}".format(str(node)))
        return node

    @classmethod
    def from_peer(cls, network_manager, currency, peer):
        '''
        Factory method to get a node from a peer document.

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param peer: The peer document
        '''
        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(network_manager, peer.currency, peer.endpoints, "", "", 0,
                   Node.ONLINE, time.time())
        logging.debug("Node from peer : {:}".format(str(node)))
        return node

    @classmethod
    def from_json(cls, network_manager, currency, data):
        endpoints = []
        uid = ""
        pubkey = ""
        block = 0
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

        if 'block' in data:
            block = data['block']

        if 'state' in data:
            state = data['state']
        else:
            logging.debug("Error : no state in node")

        node = cls(network_manager, currency, endpoints,
                   uid, pubkey, block,
                   state, last_change)
        logging.debug("Node from json : {:}".format(str(node)))
        return node

    def jsonify_root_node(self):
        logging.debug("Saving root node : {:}".format(str(self)))
        data = {'pubkey': self._pubkey,
                'uid': self._uid,
                'currency': self._currency}
        endpoints = []
        for e in self._endpoints:
            endpoints.append(e.inline())
        data['endpoints'] = endpoints
        return data

    def jsonify(self):
        logging.debug("Saving node : {:}".format(str(self)))
        data = {'pubkey': self._pubkey,
                'uid': self._uid,
                'currency': self._currency,
                'state': self._state,
                'last_change': self._last_change,
                'block': self.block}
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

    @block.setter
    def block(self, new_block):
        self._block = new_block

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

    @state.setter
    def state(self, new_state):
        logging.debug("{:} | Last state : {:} / new state : {:}".format(self.pubkey[:5],
                                                                        self.state, new_state))
        if self._state != new_state:
            self.last_change = time.time()
        self._state = new_state

    def check_sync(self, block):
        logging.debug("Check sync")
        if self.block < block:
            self.state = Node.DESYNCED
        else:
            self.state = Node.ONLINE

    def check_noerror(self, error_code, status_code):
        if error_code != QNetworkReply.NoError:
            if self.state == Node.OFFLINE:
                self.state = Node.ONLINE
            return False
        if status_code == 503:
            return False
        return True

    @pyqtSlot()
    def refresh(self):
        logging.debug("Refresh block")
        self.refresh_block()
        logging.debug("Refresh info")
        self.refresh_informations()
        logging.debug("Refresh uid")
        self.refresh_uid()
        logging.debug("Refresh peers")
        self.refresh_peers()

    def refresh_block(self):
        conn_handler = ConnectionHandler(self.network_manager,
                                         self.endpoint.conn_handler().server,
                                         self.endpoint.conn_handler().port)

        logging.debug("Requesting {0}".format(conn_handler))
        reply = qtbma.blockchain.Current(conn_handler).get()

        reply.finished.connect(lambda: self.handle_block_reply(reply))

    @pyqtSlot()
    def handle_block_reply(self, reply):
        logging.debug("Handle block reply")
        #reply = self.sender()
        logging.debug("Found thread : {0}".format(self.thread()))
        logging.debug("Found reply : {0}".format(reply))
        logging.debug("Found sender : {0}".format(self.sender()))
        logging.debug("Found url : {0}".format(reply.url().toString()))
        logging.debug("Found manager : {0}".format(reply.manager()))
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)
        logging.debug("Status code : {0}".format(status_code))
        logging.debug("Error : {0}".format(reply.error()))

        if self.check_noerror(reply.error(), status_code):
            if status_code == 200:
                strdata = bytes(reply.readAll()).decode('utf-8')
                block_data = json.loads(strdata)
                block_number = block_data['number']
            elif status_code == 404:
                block_number = 0

            if block_number != self.block:
                self.block = block_number
                logging.debug("Changed block {0} -> {1}".format(self.block,
                                                                     block_number))
                self.changed.emit()

        else:
            logging.debug("Error in block reply")

    def refresh_informations(self):
        conn_handler = ConnectionHandler(self.network_manager,
                                         self.endpoint.conn_handler().server,
                                         self.endpoint.conn_handler().port)

        peering_reply = qtbma.network.Peering(conn_handler).get()
        peering_reply.finished.connect(lambda: self.handle_peering_reply(peering_reply))

    @pyqtSlot()
    def handle_peering_reply(self, reply):
        logging.debug("Handle peering reply")
        reply = self.sender()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if self.check_noerror(reply.error(), status_code):
            strdata = bytes(reply.readAll()).decode('utf-8')
            peering_data = json.loads(strdata)
            node_pubkey = peering_data["pubkey"]
            node_currency = peering_data["currency"]

            change = False
            if node_pubkey != self.pubkey:
                self.pubkey = node_pubkey
                change = True

            if node_currency != self.currency:
                self.state = Node.CORRUPTED
                logging.debug("Change : new state corrupted")
                change = True

            if change:
                self.changed.emit()
        else:
            logging.debug("Error in peering reply")

    def refresh_uid(self):
        conn_handler = ConnectionHandler(self.network_manager,
                                         self.endpoint.conn_handler().server,
                                         self.endpoint.conn_handler().port)
        uid_reply = qtbma.wot.Lookup(conn_handler, self.pubkey).get()
        uid_reply.finished.connect(lambda: self.handle_uid_reply(uid_reply))
        uid_reply.error.connect(lambda code: logging.debug("Error : {0}".format(code)))

    @pyqtSlot()
    def handle_uid_reply(self, reply):
        logging.debug("Handle uid reply")
        #reply = self.sender()
        status_code = reply.attribute( QNetworkRequest.HttpStatusCodeAttribute );

        if self.check_noerror(reply.error(), status_code):
            uid = ''
            if status_code == 200:
                strdata = bytes(reply.readAll()).decode('utf-8')
                data = json.loads(strdata)
                timestamp = 0
                for result in data['results']:
                    if result["pubkey"] == self.pubkey:
                        uids = result['uids']
                        for uid in uids:
                            if uid["meta"]["timestamp"] > timestamp:
                                timestamp = uid["meta"]["timestamp"]
                                uid = uid["uid"]
            elif status_code == 404:
                logging.debug("UID not found")

            if self._uid != uid:
                self._uid = uid
                self.changed.emit()
        else:
            logging.debug("error in uid reply")

    def refresh_peers(self):
        conn_handler = ConnectionHandler(self.network_manager,
                                         self.endpoint.conn_handler().server,
                                         self.endpoint.conn_handler().port)

        reply = qtbma.network.peering.Peers(conn_handler).get(leaves='true')
        reply.finished.connect(lambda: self.handle_peers_reply(reply))
        reply.error.connect(lambda code: logging.debug("Error : {0}".format(code)))


    @pyqtSlot()
    def handle_peers_reply(self, reply):
        logging.debug("Handle peers reply")
        #reply = self.sender()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if self.check_noerror(reply.error(), status_code):
            strdata = bytes(reply.readAll()).decode('utf-8')
            peers_data = json.loads(strdata)
            if True: #peers_data['root'] != self._last_root:
                leaves = [leaf for leaf in peers_data['leaves']]
                          #if leaf not in self._last_leaves]
                for leaf_hash in leaves:
                    conn_handler = ConnectionHandler(self.network_manager,
                                                     self.endpoint.conn_handler().server,
                                                     self.endpoint.conn_handler().port)
                    leaf_reply = qtbma.network.peering.Peers(conn_handler).get(leaf=leaf_hash)
                    leaf_reply.finished.connect(lambda: self.handle_leaf_reply(leaf_reply))
        else:
            logging.debug("Error in peers reply")

    @pyqtSlot()
    def handle_leaf_reply(self, reply):
        logging.debug("Handle leaf reply")
        reply = self.sender()
        status_code = reply.attribute(QNetworkRequest.HttpStatusCodeAttribute)

        if self.check_noerror(reply.error(), status_code):
            strdata = bytes(reply.readAll()).decode('utf-8')
            leaf_data = json.loads(strdata)
            doc = Peer.from_signed_raw("{0}{1}\n".format(leaf_data['leaf']['value']['raw'],
                                                        leaf_data['leaf']['value']['signature']))
            self.neighbour_found.emit(doc)
        else:
            logging.debug("Error in leaf reply")

    def __str__(self):
        return ','.join([str(self.pubkey), str(self.endpoint.server), str(self.endpoint.port), str(self.block),
                         str(self.currency), str(self.state), str(self.neighbours)])
