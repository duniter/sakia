"""
Created on 21 févr. 2015

@author: inso
"""

from ucoinpy.documents.peer import Peer, Endpoint, BMAEndpoint
from ucoinpy.documents import Block, BlockId, MalformedDocumentError
from ...tools.exceptions import InvalidNodeCurrency
from ...tools.decorators import asyncify
from ucoinpy.api import bma as bma
from ucoinpy.api.bma import ConnectionHandler

from aiohttp.errors import WSClientDisconnectedError, WSServerHandshakeError, ClientResponseError
from aiohttp.errors import ClientError, DisconnectedError
from asyncio import TimeoutError
import logging
import time
import jsonschema
import asyncio
import aiohttp
from pkg_resources import parse_version
from socket import gaierror

from PyQt5.QtCore import QObject, pyqtSignal


class Node(QObject):
    """
    A node is a peer send from the client point of view.
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
    error = pyqtSignal()
    identity_changed = pyqtSignal()
    neighbour_found = pyqtSignal(Peer, str)

    def __init__(self, peer, uid, pubkey, block,
                 state, last_change, last_merkle, software, version, fork_window):
        """
        Constructor
        """
        super().__init__()
        self._peer = peer
        self._uid = uid
        self._pubkey = pubkey
        self._block = block
        self.main_chain_previous_block = None
        self._state = state
        self._neighbours = []
        self._last_change = last_change
        self._last_merkle = last_merkle
        self._software = software
        self._version = version
        self._fork_window = fork_window
        self._refresh_counter = 19
        self._ws_tasks = {'block': None,
                    'peer': None}
        self._connected = {'block': False,
                    'peer': False}

    def __del__(self):
        for ws in self._ws_tasks.values():
            if ws:
                ws.cancel()

    @classmethod
    async def from_address(cls, currency, address, port):
        """
        Factory method to get a node from a given address

        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param str address: The node address
        :param int port: The node port
        :return: A new node
        :rtype: sakia.core.net.Node
        """
        peer_data = await bma.network.Peering(ConnectionHandler(address, port)).get()

        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                  peer_data['signature']))

        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer,
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
        :rtype: sakia.core.net.Node
        """
        if currency is not None:
            if peer.currency != currency:
                raise InvalidNodeCurrency(peer.currency, currency)

        node = cls(peer, "", pubkey, None,
                   Node.OFFLINE, time.time(),
                   {'root': "", 'leaves': []},
                   "", "", 0)
        logging.debug("Node from peer : {:}".format(str(node)))
        return node

    @classmethod
    def from_json(cls, currency, data, file_version):
        """
        Loads a node from json data

        :param str currency: the currency of the community
        :param dict data: the json data of the node
        :param NormalizedVersion file_version: the version of the file
        :return: A new node
        :rtype: Node
        """
        endpoints = []
        uid = ""
        pubkey = ""
        software = ""
        version = ""
        fork_window = 0
        block = None
        last_change = time.time()
        state = Node.OFFLINE
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

        if parse_version("0.11") <= file_version < parse_version("0.12dev1") :
            for endpoint_data in data['endpoints']:
                endpoints.append(Endpoint.from_inline(endpoint_data))

            if currency in data:
                currency = data['currency']

            peer = Peer("1", currency, pubkey, BlockId(0, Block.Empty_Hash), endpoints, "SOMEFAKESIGNATURE")
        else:
            peer = Peer.from_signed_raw(data['peer'])

        node = cls(peer, uid, pubkey, block,
                   state, last_change,
                   {'root': "", 'leaves': []},
                   software, version, fork_window)

        logging.debug("Node from json : {:}".format(str(node)))
        return node

    def jsonify_root_node(self):
        logging.debug("Saving root node : {:}".format(str(self)))
        data = {'pubkey': self._pubkey,
                'uid': self._uid,
                'peer': self._peer.signed_raw()}
        return data

    def jsonify(self):
        logging.debug("Saving node : {:}".format(str(self)))
        data = {'pubkey': self._pubkey,
                'uid': self._uid,
                'peer': self._peer.signed_raw(),
                'state': self._state,
                'last_change': self._last_change,
                'block': self.block,
                'software': self._software,
                'version': self._version,
                'fork_window': self._fork_window
                }
        return data

    async def close_ws(self):
        for ws in self._ws_tasks.values():
            if ws:
                ws.cancel()
                await asyncio.sleep(0)
        closed = False
        while not closed:
            for ws in self._ws_tasks.values():
                if ws:
                    closed = False
                    break
            else:
                closed = True
            await asyncio.sleep(0)
        await asyncio.sleep(0)

    @property
    def pubkey(self):
        return self._pubkey

    @property
    def endpoint(self) -> BMAEndpoint:
        return next((e for e in self._peer.endpoints if type(e) is BMAEndpoint))

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
        return self._peer.currency

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

    @property
    def peer(self):
        return self._peer

    @peer.setter
    def peer(self, new_peer):
        if self._peer != new_peer:
            self._peer = new_peer
            self.changed.emit()

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
        #logging.debug("{:} | Changed state : {:}".format(self.pubkey[:5],
        #                                                val))
        self._last_change = val

    @state.setter
    def state(self, new_state):
        #logging.debug("{:} | Last state : {:} / new state : {:}".format(self.pubkey[:5],
        #                                                               self.state, new_state))

        if self._state != new_state:
            self.last_change = time.time()
            self._state = new_state
            self.changed.emit()
        if new_state in (Node.OFFLINE, Node.ONLINE):
            self.error.emit()

    @property
    def fork_window(self):
        return self._fork_window

    @fork_window.setter
    def fork_window(self, new_fork_window):
        if self._fork_window != new_fork_window:
            self._fork_window = new_fork_window
            self.changed.emit()

    def refresh(self, manual=False):
        """
        Refresh all data of this node
        :param bool manual: True if the refresh was manually initiated
        """
        if not self._ws_tasks['block']:
            self._ws_tasks['block'] = asyncio.ensure_future(self.connect_current_block())

        if not self._ws_tasks['peer']:
            self._ws_tasks['peer'] = asyncio.ensure_future(self.connect_peers())

        if self._refresh_counter % 20 == 0 or manual:
            self.refresh_informations()
            self.refresh_uid()
            self.refresh_summary()
            self._refresh_counter = self._refresh_counter if manual else 1
        else:
            self._refresh_counter += 1

    async def connect_current_block(self):
        """
        Connects to the websocket entry point of the node
        If the connection fails, it tries the fallback mode on HTTP GET
        """
        if not self._connected['block']:
            try:
                conn_handler = self.endpoint.conn_handler()
                block_websocket = bma.ws.Block(conn_handler)
                ws_connection = block_websocket.connect()
                async with ws_connection as ws:
                    self._connected['block'] = True
                    logging.debug("Connected successfully to block ws : {0}".format(self.pubkey[:5]))
                    async for msg in ws:
                        if msg.tp == aiohttp.MsgType.text:
                            logging.debug("Received a block : {0}".format(self.pubkey[:5]))
                            block_data = block_websocket.parse_text(msg.data)
                            await self.refresh_block(block_data)
                        elif msg.tp == aiohttp.MsgType.closed:
                            break
                        elif msg.tp == aiohttp.MsgType.error:
                            break
            except ValueError as e:
                logging.debug("Websocket block {0} : {1} - {2}".format(type(e).__name__, str(e), self.pubkey[:5]))
                await self.request_current_block()
            except (WSServerHandshakeError, WSClientDisconnectedError, ClientResponseError) as e:
                logging.debug("Websocket block {0} : {1} - {2}".format(type(e).__name__, str(e), self.pubkey[:5]))
                await self.request_current_block()
            except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
                logging.debug("{0} : {1}".format(str(e), self.pubkey[:5]))
                self.state = Node.OFFLINE
            except jsonschema.ValidationError as e:
                logging.debug(str(e))
                logging.debug("Validation error : {0}".format(self.pubkey[:5]))
                self.state = Node.CORRUPTED
            finally:
                self._connected['block'] = False
                self._ws_tasks['block'] = None

    async def request_current_block(self):
        """
        Request a node on the HTTP GET interface
        If an error occurs, the node is considered offline
        """
        try:
            conn_handler = self.endpoint.conn_handler()
            block_data = await bma.blockchain.Current(conn_handler).get()
            await self.refresh_block(block_data)
        except ValueError as e:
            if '404' in str(e):
                self.main_chain_previous_block = None
                self.set_block(None)
            else:
                self.state = Node.OFFLINE
            logging.debug("Error in block reply :  {0}".format(self.pubkey[:5]))
            logging.debug(str(e))
            self.changed.emit()
        except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
            logging.debug("{0} : {1}".format(str(e), self.pubkey[:5]))
            self.state = Node.OFFLINE
        except jsonschema.ValidationError as e:
            logging.debug(str(e))
            logging.debug("Validation error : {0}".format(self.pubkey[:5]))
            self.state = Node.CORRUPTED

    async def refresh_block(self, block_data):
        """
        Refresh the blocks of this node
        :param dict block_data: The block data in json format
        """
        conn_handler = self.endpoint.conn_handler()

        logging.debug("Requesting {0}".format(conn_handler))
        block_hash = block_data['hash']
        self.state = Node.ONLINE

        if not self.block or block_hash != self.block['hash']:
            try:
                if self.block:
                    self.main_chain_previous_block = await bma.blockchain.Block(conn_handler,
                                                                                 self.block['number']).get()
            except ValueError as e:
                if '404' in str(e):
                    self.main_chain_previous_block = None
                else:
                    self.state = Node.OFFLINE
                logging.debug("Error in previous block reply :  {0}".format(self.pubkey[:5]))
                logging.debug(str(e))
                self.changed.emit()
            except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
                logging.debug("{0} : {1}".format(str(e), self.pubkey[:5]))
                self.state = Node.OFFLINE
            except jsonschema.ValidationError as e:
                logging.debug(str(e))
                logging.debug("Validation error : {0}".format(self.pubkey[:5]))
                self.state = Node.CORRUPTED
            finally:
                self.set_block(block_data)
                logging.debug("Changed block {0} -> {1}".format(self.block['number'],
                                                                block_data['number']))
                self.changed.emit()

    @asyncify
    async def refresh_informations(self):
        """
        Refresh basic information (pubkey and currency)
        """
        conn_handler = self.endpoint.conn_handler()

        try:
            peering_data = await bma.network.Peering(conn_handler).get()
            node_pubkey = peering_data["pubkey"]
            node_currency = peering_data["currency"]
            self.state = Node.ONLINE

            if peering_data['raw'] != self.peer.raw():
                peer = Peer.from_signed_raw("{0}{1}\n".format(peering_data['raw'], peering_data['signature']))
                if peer.blockid.number > peer.blockid.number:
                    self.peer = Peer.from_signed_raw("{0}{1}\n".format(peering_data['raw'], peering_data['signature']))

            if node_pubkey != self.pubkey:
                self._pubkey = node_pubkey
                self.identity_changed.emit()

            if node_currency != self.currency:
                self.state = Node.CORRUPTED
                logging.debug("Change : new state corrupted")
                self.changed.emit()

        except ValueError as e:
            logging.debug("Error in peering reply : {0}".format(str(e)))
            self.state = Node.OFFLINE
            self.changed.emit()
        except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
            logging.debug("{0} : {1}".format(type(e).__name__, self.pubkey[:5]))
            self.state = Node.OFFLINE
        except jsonschema.ValidationError as e:
            logging.debug(str(e))
            logging.debug("Validation error : {0}".format(self.pubkey[:5]))
            self.state = Node.CORRUPTED

    @asyncify
    async def refresh_summary(self):
        """
        Refresh the summary of this node
        """
        conn_handler = self.endpoint.conn_handler()

        try:
            summary_data = await bma.node.Summary(conn_handler).get()
            self.software = summary_data["ucoin"]["software"]
            self.version = summary_data["ucoin"]["version"]
            self.state = Node.ONLINE
            if "forkWindowSize" in summary_data["ucoin"]:
                self.fork_window = summary_data["ucoin"]["forkWindowSize"]
            else:
                self.fork_window = 0
        except ValueError as e:
            logging.debug("Error in summary : {0}".format(e))
            self.state = Node.OFFLINE
            self.changed.emit()
        except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
            logging.debug("{0} : {1}".format(type(e).__name__, self.pubkey[:5]))
            self.state = Node.OFFLINE
        except jsonschema.ValidationError as e:
            logging.debug(str(e))
            logging.debug("Validation error : {0}".format(self.pubkey[:5]))
            self.state = Node.CORRUPTED

    @asyncify
    async def refresh_uid(self):
        """
        Refresh the node UID
        """
        conn_handler = self.endpoint.conn_handler()
        try:
            data = await bma.wot.Lookup(conn_handler, self.pubkey).get()
            self.state = Node.ONLINE
            timestamp = 0
            uid = ""
            for result in data['results']:
                if result["pubkey"] == self.pubkey:
                    uids = result['uids']
                    for uid in uids:
                        if uid["meta"]["timestamp"] > timestamp:
                            timestamp = uid["meta"]["timestamp"]
                            uid = uid["uid"]
            if self._uid != uid:
                self._uid = uid
                self.identity_changed.emit()
        except ValueError as e:
            if '404' in str(e):
                logging.debug("UID not found : {0}".format(self.pubkey[:5]))
            else:
                logging.debug("error in uid reply : {0}".format(self.pubkey[:5]))
                self.state = Node.OFFLINE
                self.identity_changed.emit()
        except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
            logging.debug("{0} : {1}".format(type(e).__name__, self.pubkey[:5]))
            self.state = Node.OFFLINE
        except jsonschema.ValidationError as e:
            logging.debug(str(e))
            logging.debug("Validation error : {0}".format(self.pubkey[:5]))
            self.state = Node.CORRUPTED

    async def connect_peers(self):
        """
        Connects to the peer websocket entry point
        If the connection fails, it tries the fallback mode on HTTP GET
        """
        if not self._connected['peer']:
            try:
                conn_handler = self.endpoint.conn_handler()
                peer_websocket = bma.ws.Peer(conn_handler)
                ws_connection = peer_websocket.connect()
                async with ws_connection as ws:
                    self._connected['peer'] = True
                    logging.debug("Connected successfully to peer ws : {0}".format(self.pubkey[:5]))
                    async for msg in ws:
                        if msg.tp == aiohttp.MsgType.text:
                            logging.debug("Received a peer : {0}".format(self.pubkey[:5]))
                            peer_data = peer_websocket.parse_text(msg.data)
                            self.refresh_peer_data(peer_data)
                        elif msg.tp == aiohttp.MsgType.closed:
                            break
                        elif msg.tp == aiohttp.MsgType.error:
                            break
            except ValueError as e:
                logging.debug("Websocket peer {0} : {1} - {2}".format(type(e).__name__, str(e), self.pubkey[:5]))
                await self.request_peers()
            except (WSServerHandshakeError, WSClientDisconnectedError, ClientResponseError) as e:
                logging.debug("Websocket peer {0} : {1} - {2}".format(type(e).__name__, str(e), self.pubkey[:5]))
                await self.request_peers()
            except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
                logging.debug("{0} : {1}".format(str(e), self.pubkey[:5]))
                self.state = Node.OFFLINE
            except jsonschema.ValidationError as e:
                logging.debug(str(e))
                logging.debug("Validation error : {0}".format(self.pubkey[:5]))
                self.state = Node.CORRUPTED
            finally:
                self._connected['peer'] = False
                self._ws_tasks['peer'] = None

    async def request_peers(self):
        """
        Refresh the list of peers knew by this node
        """
        conn_handler = self.endpoint.conn_handler()

        try:
            peers_data = await bma.network.peering.Peers(conn_handler).get(leaves='true')
            self.state = Node.ONLINE
            if peers_data['root'] != self._last_merkle['root']:
                leaves = [leaf for leaf in peers_data['leaves']
                          if leaf not in self._last_merkle['leaves']]
                for leaf_hash in leaves:
                    try:
                        leaf_data = await bma.network.peering.Peers(conn_handler).get(leaf=leaf_hash)
                        self.refresh_peer_data(leaf_data['leaf']['value'])
                    except (AttributeError, ValueError) as e:
                        logging.debug("{pubkey} : Incorrect peer data in {leaf}".format(pubkey=self.pubkey[:5],
                                                                                        leaf=leaf_hash))
                        self.state = Node.OFFLINE
                        self.changed.emit()
                    except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
                        logging.debug("{0} : {1}".format(type(e).__name__, self.pubkey[:5]))
                        self.state = Node.OFFLINE
                    except jsonschema.ValidationError as e:
                        logging.debug(str(e))
                        logging.debug("Validation error : {0}".format(self.pubkey[:5]))
                        self.state = Node.CORRUPTED
                self._last_merkle = {'root' : peers_data['root'],
                                     'leaves': peers_data['leaves']}
        except ValueError as e:
            logging.debug("Error in peers reply")
            self.state = Node.OFFLINE
            self.changed.emit()
        except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
            logging.debug("{0} : {1}".format(type(e).__name__, self.pubkey))
            self.state = Node.OFFLINE
        except jsonschema.ValidationError as e:
            logging.debug(str(e))
            logging.debug("Validation error : {0}".format(self.pubkey))
            self.state = Node.CORRUPTED

    def refresh_peer_data(self, peer_data):
        if "raw" in peer_data:
            try:
                str_doc = "{0}{1}\n".format(peer_data['raw'],
                                            peer_data['signature'])
                peer_doc = Peer.from_signed_raw(str_doc)
                pubkey = peer_data['pubkey']
                self.neighbour_found.emit(peer_doc, pubkey)
            except MalformedDocumentError as e:
                logging.debug(str(e))
        else:
            logging.debug("Incorrect leaf reply")

    def __str__(self):
        return ','.join([str(self.pubkey), str(self.endpoint.server),
                         str(self.endpoint.ipv4), str(self.endpoint.port),
                         str(self.block['number'] if self.block else "None"),
                         str(self.currency), str(self.state), str(self.neighbours)])
