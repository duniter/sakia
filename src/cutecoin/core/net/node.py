"""
Created on 21 févr. 2015

@author: inso
"""

from ucoinpy.documents.peer import Peer, Endpoint, BMAEndpoint
from ucoinpy.documents.block import Block
from ...tools.exceptions import InvalidNodeCurrency
from ...tools.decorators import asyncify
from ucoinpy.api import bma as bma
from ucoinpy.api.bma import ConnectionHandler

import asyncio
from aiohttp.errors import ClientError
import logging
import time
import json

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QNetworkReply, QNetworkRequest


class Node(QObject):
    """
    A node is a peer seend from the client point of view.
    This node can have multiple states :
    - ONLINE : The node is available for requests
    - OFFLINE: The node is disconnected
    - DESYNCED : The node is online but is desynced from the network
    - CORRUPTED : The node is corrupted, some weird behaviour is going on
    """

    ONLINE = 1
    OFFLINE = 2
    DESYNCED = 3
    CORRUPTED = 4

    changed = pyqtSignal()
    neighbour_found = pyqtSignal(Peer, str)

    def __init__(self, currency, endpoints, uid, pubkey, block,
                 state, last_change, last_merkle, software, version, fork_window):
        """
        Constructor
        """
        super().__init__()
        self._endpoints = endpoints
        self._uid = uid
        self._pubkey = pubkey
        self._block = block
        self._state = state
        self._neighbours = []
        self._currency = currency
        self._last_change = last_change
        self._last_merkle = last_merkle
        self._software = software
        self._version = version
        self._fork_window = fork_window

    @classmethod
    @asyncio.coroutine
    def from_address(cls, currency, address, port):
        """
        Factory method to get a node from a given address

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param str address: The node address
        :param int port: The node port
        :return: A new node
        :rtype: cutecoin.core.net.Node
        """
        peer_data = yield from bma.network.Peering(ConnectionHandler(address, port)).get()

        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                  peer_data['signature']))

        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer.currency,
                   [Endpoint.from_inline(e.inline()) for e in peer.endpoints],
                   "", peer.pubkey, None, Node.ONLINE, time.time(),
                   {'root': "", 'leaves': []}, "", "", 0)
        logging.debug("Node from address : {:}".format(str(node)))
        return node

    @classmethod
    def from_peer(cls, currency, peer, pubkey):
        """
        Factory method to get a node from a peer document.

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param peer: The peer document
        :return: A new node
        :rtype: cutecoin.core.net.Node
        """
        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer.currency, peer.endpoints,
                   "", pubkey, None,
                   Node.ONLINE, time.time(),
                   {'root': "", 'leaves': []},
                   "", "", 0)
        logging.debug("Node from peer : {:}".format(str(node)))
        return node

    @classmethod
    def from_json(cls, currency, data):
        endpoints = []
        uid = ""
        pubkey = ""
        software = ""
        version = ""
        fork_window = 0
        block = None
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

        if 'software' in data:
            software = data['software']

        if 'version' in data:
            version = data['version']

        if 'fork_window' in data:
            fork_window = data['fork_window']

        node = cls(currency, endpoints,
                   uid, pubkey, block,
                   state, last_change,
                   {'root': "", 'leaves': []},
                   software, version, fork_window)
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
                'block': self.block,
                'software': self._software,
                'version': self._version,
                'fork_window': self._fork_window
                }
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

    def set_block(self, block):
        self._block = block

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

    @property
    def software(self):
        return self._software

    @software.setter
    def software(self, new_soft):
        if self._software != new_soft:
            self._software = new_soft
            self.changed.emit()

    @property
    def version(self):
        return self._version

    @version.setter
    def version(self, new_version):
        if self._version != new_version:
            self._version = new_version
            self.changed.emit()

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
            self.changed.emit()

    @property
    def fork_window(self):
        return self._fork_window

    @fork_window.setter
    def fork_window(self, new_fork_window):
        if self._fork_window != new_fork_window:
            self._fork_window = new_fork_window
            self.changed.emit()

    @pyqtSlot()
    def refresh(self):
        """
        Refresh all data of this node
        """
        logging.debug("Refresh block")
        self.refresh_block()
        logging.debug("Refresh info")
        self.refresh_informations()
        logging.debug("Refresh uid")
        self.refresh_uid()
        logging.debug("Refresh peers")
        self.refresh_peers()
        logging.debug("Refresh summary")
        self.refresh_summary()

    @asyncify
    @asyncio.coroutine
    def refresh_block(self):
        """
        Refresh the blocks of this node
        """
        conn_handler = self.endpoint.conn_handler()

        logging.debug("Requesting {0}".format(conn_handler))
        try:
            block_data = yield from bma.blockchain.Current(conn_handler).get()
            block_hash = block_data['hash']
            self.state = Node.ONLINE

            if not self.block or block_hash != self.block['hash']:
                self.set_block(block_data)
                logging.debug("Changed block {0} -> {1}".format(self.block['number'],
                                                                block_data['number']))
                self.changed.emit()
        except ValueError as e:
            if '404' in str(e):
                self.set_block(None)
            logging.debug("Error in block reply")
            self.changed.emit()
        except ClientError:
            logging.debug("Client error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE
        except asyncio.TimeoutError:
            logging.debug("Timeout error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE

    @asyncify
    @asyncio.coroutine
    def refresh_informations(self):
        """
        Refresh basic information (pubkey and currency)
        """
        conn_handler = self.endpoint.conn_handler()

        try:
            peering_data = yield from bma.network.Peering(conn_handler).get()
            logging.debug(peering_data)
            node_pubkey = peering_data["pubkey"]
            node_currency = peering_data["currency"]
            self.state = Node.ONLINE

            change = False
            if node_pubkey != self.pubkey:
                self._pubkey = node_pubkey
                change = True

            if node_currency != self.currency:
                self.state = Node.CORRUPTED
                logging.debug("Change : new state corrupted")
                change = True

            if change:
                self.changed.emit()
        except ValueError as e:
            logging.debug("Error in peering reply : {0}".format(str(e)))
            self.changed.emit()
        except ClientError:
            logging.debug("Client error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE
        except asyncio.TimeoutError:
            logging.debug("Timeout error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE

    @asyncify
    @asyncio.coroutine
    def refresh_summary(self):
        """
        Refresh the summary of this node
        """
        conn_handler = self.endpoint.conn_handler()

        try:
            summary_data = yield from bma.node.Summary(conn_handler).get()
            self.software = summary_data["ucoin"]["software"]
            self.version = summary_data["ucoin"]["version"]
            self.state = Node.ONLINE
            if "forkWindowSize" in summary_data["ucoin"]:
                self.fork_window = summary_data["ucoin"]["forkWindowSize"]
            else:
                self.fork_window = 0
        except ValueError as e:
            logging.debug("Error in summary : {0}".format(e))
            self.changed.emit()
        except ClientError:
            logging.debug("Client error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE
        except asyncio.TimeoutError:
            logging.debug("Timeout error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE

    @asyncify
    @asyncio.coroutine
    def refresh_uid(self):
        """
        Refresh the node UID
        """
        conn_handler = self.endpoint.conn_handler()
        try:
            data = yield from bma.wot.Lookup(conn_handler, self.pubkey).get()
            self.state = Node.ONLINE
            timestamp = 0
            uid = None
            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    uids = result['uids']
                    for uid in uids:
                        if uid["meta"]["timestamp"] > timestamp:
                            timestamp = uid["meta"]["timestamp"]
                            uid = uid["uid"]
            if uid and self._uid != uid:
                self._uid = uid
                self.changed.emit()
        except ValueError as e:
            if '404' in str(e):
                logging.debug("UID not found")
            else:
                logging.debug("error in uid reply")
                self.changed.emit()
        except ClientError:
            logging.debug("Client error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE
        except asyncio.TimeoutError:
            logging.debug("Timeout error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE

    @asyncify
    @asyncio.coroutine
    def refresh_peers(self):
        """
        Refresh the list of peers knew by this node
        """
        conn_handler = self.endpoint.conn_handler()

        try:
            peers_data = yield from bma.network.peering.Peers(conn_handler).get(leaves='true')
            self.state = Node.ONLINE
            if peers_data['root'] != self._last_merkle['root']:
                leaves = [leaf for leaf in peers_data['leaves']
                          if leaf not in self._last_merkle['leaves']]
                for leaf_hash in leaves:
                    try:
                        leaf_data = yield from bma.network.peering.Peers(conn_handler).get(leaf=leaf_hash)
                        if "raw" in leaf_data['leaf']['value']:
                            peer_doc = Peer.from_signed_raw("{0}{1}\n".format(leaf_data['leaf']['value']['raw'],
                                                                        leaf_data['leaf']['value']['signature']))
                            pubkey = leaf_data['leaf']['value']['pubkey']
                            self.neighbour_found.emit(peer_doc, pubkey)
                        else:
                            logging.debug("Incorrect leaf reply")
                    except ValueError as e:
                        logging.debug("Error in leaf reply")
                        self.changed.emit()
                self._last_merkle = {'root' : peers_data['root'],
                                     'leaves': peers_data['leaves']}
        except ValueError as e:
            logging.debug("Error in peers reply")
            self.changed.emit()
        except ClientError:
            logging.debug("Client error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE
        except asyncio.TimeoutError:
            logging.debug("Timeout error : {0}".format(self.pubkey))
            self.state = Node.OFFLINE

    def __str__(self):
        return ','.join([str(self.pubkey), str(self.endpoint.server),
                         str(self.endpoint.ipv4), str(self.endpoint.port),
                         str(self.block['number'] if self.block else "None"),
                         str(self.currency), str(self.state), str(self.neighbours)])
