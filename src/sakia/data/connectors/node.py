import asyncio
import logging
from asyncio import TimeoutError
from socket import gaierror

import aiohttp
import jsonschema
from PyQt5.QtCore import QObject, pyqtSignal
from aiohttp.errors import ClientError, DisconnectedError
from aiohttp.errors import WSClientDisconnectedError, WSServerHandshakeError, ClientResponseError

from duniterpy.api import bma, errors
from duniterpy.documents import BlockUID, MalformedDocumentError, BMAEndpoint
from duniterpy.documents.peer import Peer
from sakia.decorators import asyncify
from sakia.errors import InvalidNodeCurrency
from ..entities.node import Node


class NodeConnector(QObject):
    """
    A node is a peer send from the client point of view.
    """
    changed = pyqtSignal()
    error = pyqtSignal()
    identity_changed = pyqtSignal()
    neighbour_found = pyqtSignal(Peer)

    def __init__(self, node, session):
        """
        Constructor
        """
        super().__init__()
        self.node = node
        self._ws_tasks = {'block': None,
                    'peer': None}
        self._connected = {'block': False,
                    'peer': False}
        self._session = session
        self._refresh_counter = 1

    def __del__(self):
        for ws in self._ws_tasks.values():
            if ws:
                ws.cancel()

    @property
    def session(self):
        return self._session

    @classmethod
    def from_peer(cls, currency, peer, session):
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

        node = Node(peer.currency, peer.pubkey, peer.endpoints, peer.blockUID)
        logging.debug("Node from peer : {:}".format(str(node)))

        return cls(node, session)

    async def _safe_request(self, endpoint, request, req_args={}, get_args={}):
        try:
            conn_handler = endpoint.conn_handler()
            data = await request(conn_handler, **req_args).get(self._session, **get_args)
            return data
        except (ClientError, gaierror, TimeoutError, ConnectionRefusedError, DisconnectedError, ValueError) as e:
            logging.debug("{0} : {1}".format(str(e), self.node.pubkey[:5]))
            self.node.state = Node.OFFLINE
        except jsonschema.ValidationError as e:
            logging.debug(str(e))
            logging.debug("Validation error : {0}".format(self.node.pubkey[:5]))
            self.node.state = Node.CORRUPTED

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

    def refresh(self, manual=False):
        """
        Refresh all data of this node
        :param bool manual: True if the refresh was manually initiated
        """
        if not self._ws_tasks['block']:
            self._ws_tasks['block'] = asyncio.ensure_future(self.connect_current_block())

        if not self._ws_tasks['peer']:
            self._ws_tasks['peer'] = asyncio.ensure_future(self.connect_peers())

        if manual:
            asyncio.ensure_future(self.request_peers())

        if self._refresh_counter % 20 == 0 or manual:
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
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            if not self._connected['block']:
                try:
                    conn_handler = endpoint.conn_handler()
                    block_websocket = bma.ws.Block(conn_handler)
                    ws_connection = block_websocket.connect(self._session)
                    async with ws_connection as ws:
                        self._connected['block'] = True
                        logging.debug("Connected successfully to block ws : {0}"
                                      .format(self.node.pubkey[:5]))
                        async for msg in ws:
                            if msg.tp == aiohttp.MsgType.text:
                                logging.debug("Received a block : {0}".format(self.node.pubkey[:5]))
                                block_data = block_websocket.parse_text(msg.data)
                                await self.refresh_block(block_data)
                            elif msg.tp == aiohttp.MsgType.closed:
                                break
                            elif msg.tp == aiohttp.MsgType.error:
                                break
                except (WSServerHandshakeError, WSClientDisconnectedError,
                        ClientResponseError, ValueError) as e:
                    logging.debug("Websocket block {0} : {1} - {2}"
                                  .format(type(e).__name__, str(e), self.node.pubkey[:5]))
                    await self.request_current_block()
                except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
                    logging.debug("{0} : {1}".format(str(e), self.node.pubkey[:5]))
                    self.node.state = Node.OFFLINE
                except jsonschema.ValidationError as e:
                    logging.debug(str(e))
                    logging.debug("Validation error : {0}".format(self.node.pubkey[:5]))
                    self.node.state = Node.CORRUPTED
                finally:
                    self.changed.emit()
                    self._connected['block'] = False
                    self._ws_tasks['block'] = None

    async def request_current_block(self):
        """
        Request a node on the HTTP GET interface
        If an error occurs, the node is considered offline
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                block_data = await self._safe_request(endpoint, bma.blockchain.Current, self._session)
                await self.refresh_block(block_data)
                return  # Do not try any more endpoint
            except errors.DuniterError as e:
                if e.ucode == errors.BLOCK_NOT_FOUND:
                    self.node.previous_buid = BlockUID.empty()
                else:
                    self.node.state = Node.OFFLINE
                logging.debug("Error in block reply of {0} : {1}}".format(self.node.pubkey[:5], str(e)))
            finally:
                self.changed.emit()
        else:
            logging.debug("Could not connect to any BMA endpoint : {0}".format(self.node.pubkey[:5]))
            self.node.state = Node.OFFLINE
            self.changed.emit()

    async def refresh_block(self, block_data):
        """
        Refresh the blocks of this node
        :param dict block_data: The block data in json format
        """
        self.node.state = Node.ONLINE
        if not self.node.current_buid or self.node.current_buid.sha_hash != block_data['hash']:
            for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
                conn_handler = endpoint.conn_handler()
                logging.debug("Requesting {0}".format(conn_handler))
                try:
                    previous_block = await self._safe_request(endpoint, bma.blockchain.Block,
                                                              req_args={'number': self.node.current_buid.number})
                    self.node.previous_buid = BlockUID(previous_block['number'], previous_block['hash'])
                    return  # Do not try any more endpoint
                except errors.DuniterError as e:
                    if e.ucode == errors.BLOCK_NOT_FOUND:
                        self.node.previous_buid = BlockUID.empty()
                        self.node.current_buid = BlockUID.empty()
                    else:
                        self.node.state = Node.OFFLINE
                    logging.debug("Error in previous block reply of {0} : {1}".format(self.node.pubkey[:5], str(e)))
                finally:
                    self.node.current_buid = BlockUID(block_data['number'], block_data['hash'])
                    logging.debug("Changed block {0} -> {1}".format(self.node.current_buid.number,
                                                                    block_data['number']))
                    self.changed.emit()
            else:
                logging.debug("Could not connect to any BMA endpoint : {0}".format(self.node.pubkey[:5]))
                self.node.state = Node.OFFLINE
                self.changed.emit()

    @asyncify
    async def refresh_summary(self):
        """
        Refresh the summary of this node
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                summary_data = await self._safe_request(endpoint, bma.node.Summary)
                self.node.software = summary_data["duniter"]["software"]
                self.node.version = summary_data["duniter"]["version"]
                self.node.state = Node.ONLINE
                return  # Break endpoints loop
            except errors.DuniterError as e:
                self.node.state = Node.OFFLINE
                logging.debug("Error in summary of {0} : {1}".format(self.node.pubkey[:5], str(e)))
            finally:
                self.changed.emit()
        else:
            logging.debug("Could not connect to any BMA endpoint : {0}".format(self.node.pubkey[:5]))
            self.node.state = Node.OFFLINE
            self.changed.emit()

    @asyncify
    async def refresh_uid(self):
        """
        Refresh the node UID
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                data = await self._safe_request(endpoint, bma.wot.Lookup,
                                                req_args={'search':self.node.pubkey},
                                                get_args={})
                self.node.state = Node.ONLINE
                timestamp = BlockUID.empty()
                uid = ""
                for result in data['results']:
                    if result["pubkey"] == self.node.pubkey:
                        uids = result['uids']
                        for uid in uids:
                            if BlockUID.from_str(uid["meta"]["timestamp"]) >= timestamp:
                                timestamp = uid["meta"]["timestamp"]
                                uid = uid["uid"]
                if self.node.uid != uid:
                    self.node.uid = uid
                    self.identity_changed.emit()
            except errors.DuniterError as e:
                if e.ucode == errors.NO_MATCHING_IDENTITY:
                    logging.debug("UID not found : {0}".format(self.node.pubkey[:5]))
                else:
                    logging.debug("error in uid reply : {0}".format(self.node.pubkey[:5]))
                    self.node.state = Node.OFFLINE
                    self.identity_changed.emit()
        else:
            logging.debug("Could not connect to any BMA endpoint : {0}".format(self.node.pubkey[:5]))
            self.node.state = Node.OFFLINE
            self.changed.emit()

    async def connect_peers(self):
        """
        Connects to the peer websocket entry point
        If the connection fails, it tries the fallback mode on HTTP GET
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            if not self._connected['peer']:
                try:
                    conn_handler = endpoint.conn_handler()
                    peer_websocket = bma.ws.Peer(conn_handler)
                    ws_connection = peer_websocket.connect(self._session)
                    async with ws_connection as ws:
                        self._connected['peer'] = True
                        logging.debug("Connected successfully to peer ws : {0}".format(self.node.pubkey[:5]))
                        async for msg in ws:
                            if msg.tp == aiohttp.MsgType.text:
                                logging.debug("Received a peer : {0}".format(self.node.pubkey[:5]))
                                peer_data = peer_websocket.parse_text(msg.data)
                                self.refresh_peer_data(peer_data)
                            elif msg.tp == aiohttp.MsgType.closed:
                                break
                            elif msg.tp == aiohttp.MsgType.error:
                                break
                except (WSServerHandshakeError, WSClientDisconnectedError,
                        ClientResponseError, ValueError) as e:
                    logging.debug("Websocket peer {0} : {1} - {2}"
                                  .format(type(e).__name__, str(e), self.node.pubkey[:5]))
                    await self.request_peers()
                except (ClientError, gaierror, TimeoutError, DisconnectedError) as e:
                    logging.debug("{0} : {1}".format(str(e), self.node.pubkey[:5]))
                    self.node.state = Node.OFFLINE
                except jsonschema.ValidationError as e:
                    logging.debug(str(e))
                    logging.debug("Validation error : {0}".format(self.node.pubkey[:5]))
                    self.node.state = Node.CORRUPTED
                finally:
                    self._connected['peer'] = False
                    self._ws_tasks['peer'] = None
                    self.changed.emit()
        else:
            logging.debug("Could not connect to any BMA endpoint : {0}".format(self.node.pubkey[:5]))
            self.node.state = Node.OFFLINE
            self.changed.emit()

    async def request_peers(self):
        """
        Refresh the list of peers knew by this node
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                peers_data = await self._safe_request(endpoint, bma.network.peering.Peers,
                                                      get_args={'leaves': 'true'})
                self.node.state = Node.ONLINE
                if peers_data['root'] != self.node.merkle_peers_root:
                    leaves = [leaf for leaf in peers_data['leaves']
                              if leaf not in self.node.merkle_peers_leaves]
                    for leaf_hash in leaves:
                        try:
                            leaf_data = await self._safe_request(endpoint,
                                                                 bma.network.peering.Peers,
                                                                 get_args={'leaf': leaf_hash})
                            self.refresh_peer_data(leaf_data['leaf']['value'])
                        except (AttributeError, ValueError, errors.DuniterError) as e:
                            logging.debug("{pubkey} : Incorrect peer data in {leaf}"
                                          .format(pubkey=self.node.pubkey[:5],
                                                  leaf=leaf_hash))
                            self.node.state = Node.OFFLINE
                        finally:
                            self.changed.emit()
                    self.node.merkle_peers_root = tuple(peers_data['root'])
                    self.node.merkle_peers_leaves = tuple(peers_data['leaves'])
                return  # Break endpoints loop
            except errors.DuniterError as e:
                logging.debug("Error in peers reply : {0}".format(str(e)))
                self.node.state = Node.OFFLINE
            finally:
                self.changed.emit()
        else:
            logging.debug("Could not connect to any BMA endpoint : {0}".format(self.node.pubkey[:5]))
            self.node.state = Node.OFFLINE
            self.changed.emit()

    def refresh_peer_data(self, peer_data):
        if "raw" in peer_data:
            try:
                str_doc = "{0}{1}\n".format(peer_data['raw'],
                                            peer_data['signature'])
                peer_doc = Peer.from_signed_raw(str_doc)
                self.neighbour_found.emit(peer_doc)
            except MalformedDocumentError as e:
                logging.debug(str(e))
        else:
            logging.debug("Incorrect leaf reply")