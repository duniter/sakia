import asyncio
import logging
import time
from asyncio import TimeoutError
from socket import gaierror

import aiohttp
import jsonschema
from PyQt5.QtCore import QObject, pyqtSignal
from aiohttp import ClientError

from duniterpy.api import bma, errors
from duniterpy.documents import BlockUID, MalformedDocumentError, BMAEndpoint
from duniterpy.documents.peer import Peer, ConnectionHandler
from sakia.decorators import asyncify
from sakia.errors import InvalidNodeCurrency
from ..entities.node import Node


class NodeConnectorLoggerAdapter(logging.LoggerAdapter):
    """
    This example adapter expects the passed in dict-like object to have a
    'connid' key, whose value in brackets is prepended to the log message.
    """
    def process(self, msg, kwargs):
        return '[%s] %s' % (self.extra['pubkey'][:5], msg), kwargs


class NodeConnector(QObject):
    """
    A node is a peer send from the client point of view.
    """
    changed = pyqtSignal()
    error = pyqtSignal()
    identity_changed = pyqtSignal()
    neighbour_found = pyqtSignal(Peer)

    def __init__(self, node, user_parameters, session=None):
        """
        Constructor
        """
        super().__init__()
        self.node = node
        self._ws_tasks = {'block': None,
                    'peer': None}
        self._connected = {'block': False,
                    'peer': False}
        self._user_parameters = user_parameters
        self.session = session
        self._raw_logger = logging.getLogger('sakia')
        self._logger = NodeConnectorLoggerAdapter(self._raw_logger, {'pubkey': self.node.pubkey})

    def __del__(self):
        for ws in self._ws_tasks.values():
            if ws:
                ws.cancel()

    @classmethod
    async def from_address(cls, currency, secured, address, port, user_parameters):
        """
        Factory method to get a node from a given address
        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param bool secured: True if the node uses https
        :param str address: The node address
        :param int port: The node port
        :return: A new node
        :rtype: sakia.core.net.Node
        """
        http_scheme = "https" if secured else "http"
        ws_scheme = "ws" if secured else "wss"
        session = aiohttp.ClientSession()
        peer_data = await bma.network.peering(ConnectionHandler(http_scheme, ws_scheme, address, port, "",
                                                                proxy=user_parameters.proxy(), session=session))

        peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                      peer_data['signature']))

        if currency and peer.currency != currency:
            raise InvalidNodeCurrency(currency, peer.currency)

        node = Node(peer.currency, peer.pubkey, peer.endpoints, peer.blockUID, last_state_change=time.time())
        logging.getLogger('sakia').debug("Node from address : {:}".format(str(node)))

        return cls(node, user_parameters, session=session)

    @classmethod
    def from_peer(cls, currency, peer, user_parameters):
        """
        Factory method to get a node from a peer document.
        :param str currency: The node currency. None if we don't know\
         the currency it should have, for example if its the first one we add
        :param peer: The peer document
        :return: A new node
        :rtype: sakia.core.net.Node
        """
        if currency and peer.currency != currency:
            raise InvalidNodeCurrency(currency, peer.currency)

        node = Node(peer.currency, peer.pubkey, peer.endpoints, peer.blockUID, last_state_change=time.time())
        logging.getLogger('sakia').debug("Node from peer : {:}".format(str(node)))

        return cls(node, user_parameters, session=None)

    async def safe_request(self, endpoint, request, proxy, req_args={}):
        try:
            conn_handler = next(endpoint.conn_handler(self.session, proxy=proxy))
            data = await request(conn_handler, **req_args)
            return data
        except errors.DuniterError as e:
            if e.ucode == 1006:
                self._logger.debug("{0}".format(str(e)))
            else:
                raise
        except (ClientError, gaierror, TimeoutError, ConnectionRefusedError, ValueError) as e:
            self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
            self.change_state_and_emit(Node.OFFLINE)
        except jsonschema.ValidationError as e:
            self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
            self.change_state_and_emit(Node.CORRUPTED)
        except RuntimeError:
            if self.session.closed:
                pass
            else:
                raise

    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()

    async def close_ws(self):
        for ws in self._ws_tasks.values():
            if ws:
                ws.cancel()
        closed = False
        while not closed:
            for ws in self._ws_tasks.values():
                if ws:
                    closed = False
                    break
            else:
                closed = True
            await asyncio.sleep(0)
        await self.session.close()
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

    async def connect_current_block(self):
        """
        Connects to the websocket entry point of the node
        If the connection fails, it tries the fallback mode on HTTP GET
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            if not self._connected['block']:
                try:
                    conn_handler = next(endpoint.conn_handler(self.session, proxy=self._user_parameters.proxy()))
                    ws_connection = bma.ws.block(conn_handler)
                    async with ws_connection as ws:
                        self._connected['block'] = True
                        self._logger.debug("Connected successfully to block ws")
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                self._logger.debug("Received a block")
                                block_data = bma.parse_text(msg.data, bma.ws.WS_BLOCk_SCHEMA)
                                await self.refresh_block(block_data)
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                break
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                except (aiohttp.WSServerHandshakeError, ValueError) as e:
                    self._logger.debug("Websocket block {0} : {1}".format(type(e).__name__, str(e)))
                    await self.request_current_block()
                except (ClientError, gaierror, TimeoutError) as e:
                    self._logger.debug("{0} : {1}".format(str(e), self.node.pubkey[:5]))
                    self.change_state_and_emit(Node.OFFLINE)
                except jsonschema.ValidationError as e:
                    self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
                    self.change_state_and_emit(Node.CORRUPTED)
                except RuntimeError:
                    if self.session.closed:
                        pass
                    else:
                        raise
                finally:
                    self._connected['block'] = False
                    self._ws_tasks['block'] = None

    async def request_current_block(self):
        """
        Request a node on the HTTP GET interface
        If an error occurs, the node is considered offline
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                block_data = await self.safe_request(endpoint, bma.blockchain.current,
                                                     proxy=self._user_parameters.proxy())
                if not block_data:
                    continue
                await self.refresh_block(block_data)
                return  # Do not try any more endpoint
            except errors.DuniterError as e:
                if e.ucode == errors.BLOCK_NOT_FOUND:
                    self.node.previous_buid = BlockUID.empty()
                    self.change_state_and_emit(Node.ONLINE)
                else:
                    self.change_state_and_emit(Node.CORRUPTED)
                    self._logger.debug("Error in block reply :  {0}".format(str(e)))
        else:
            if self.session.closed:
                pass
            else:
                self._logger.debug("Could not connect to any BMA endpoint")
                self.change_state_and_emit(Node.OFFLINE)

    async def refresh_block(self, block_data):
        """
        Refresh the blocks of this node
        :param dict block_data: The block data in json format
        """
        if not self.node.current_buid or self.node.current_buid.sha_hash != block_data['hash']:
            for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
                conn_handler = next(endpoint.conn_handler(self.session,
                                                     proxy=self._user_parameters.proxy()))
                self._logger.debug("Requesting {0}".format(conn_handler))
                try:
                    previous_block = await self.safe_request(endpoint, bma.blockchain.block,
                                                             proxy=self._user_parameters.proxy(),
                                                             req_args={'number': self.node.current_buid.number})
                    if not previous_block:
                        continue
                    self.node.previous_buid = BlockUID(previous_block['number'], previous_block['hash'])
                    break  # Do not try any more endpoint
                except errors.DuniterError as e:
                    if e.ucode == errors.BLOCK_NOT_FOUND:
                        self.node.previous_buid = BlockUID.empty()
                        # we don't change state here
                        break
                    else:
                        self.change_state_and_emit(Node.CORRUPTED)
                        break

                finally:
                    if self.node.current_buid != BlockUID(block_data['number'], block_data['hash']):
                        self.node.current_buid = BlockUID(block_data['number'], block_data['hash'])
                        self.node.current_ts = block_data['medianTime']
                        self._logger.debug("Changed block {0} -> {1}".format(self.node.current_buid.number,
                                                                        block_data['number']))
                        self.changed.emit()
            else:
                if self.session.closed:
                    pass
                else:
                    self._logger.debug("Could not connect to any BMA endpoint")
                    self.change_state_and_emit(Node.OFFLINE)
        else:
            self.change_state_and_emit(Node.ONLINE)

    @asyncify
    async def refresh_summary(self):
        """
        Refresh the summary of this node
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                summary_data = await self.safe_request(endpoint, bma.node.summary,
                                                       proxy=self._user_parameters.proxy())
                if not summary_data:
                    continue
                self.node.software = summary_data["duniter"]["software"]
                self.node.version = summary_data["duniter"]["version"]
                self.node.state = Node.ONLINE
                self.identity_changed.emit()
                return  # Break endpoints loop
            except errors.DuniterError as e:
                self._logger.debug("Error in summary : {:}".format(str(e)))
                self.change_state_and_emit(Node.OFFLINE)
        else:
            if self.session.closed:
                pass
            else:
                self._logger.debug("Could not connect to any BMA endpoint")
                self.change_state_and_emit(Node.OFFLINE)

    async def connect_peers(self):
        """
        Connects to the peer websocket entry point
        If the connection fails, it tries the fallback mode on HTTP GET
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            if not self._connected['peer']:
                try:
                    conn_handler = next(endpoint.conn_handler(self.session,
                                                         proxy=self._user_parameters.proxy()))
                    ws_connection = bma.ws.peer(conn_handler)
                    async with ws_connection as ws:
                        self._connected['peer'] = True
                        self._logger.debug("Connected successfully to peer ws")
                        async for msg in ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                self._logger.debug("Received a peer")
                                peer_data = bma.parse_text(msg.data, bma.ws.WS_PEER_SCHEMA)
                                self.refresh_peer_data(peer_data)
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                break
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
                except (aiohttp.WSServerHandshakeError, ValueError) as e:
                    self._logger.debug("Websocket peer {0} : {1}"
                                       .format(type(e).__name__, str(e)))
                    await self.request_peers()
                except (ClientError, gaierror, TimeoutError) as e:
                    self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
                    self.change_state_and_emit(Node.OFFLINE)
                except jsonschema.ValidationError as e:
                    self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
                    self.change_state_and_emit(Node.CORRUPTED)
                except RuntimeError:
                    if self.session.closed:
                        pass
                    else:
                        raise
                finally:
                    self._connected['peer'] = False
                    self._ws_tasks['peer'] = None

    async def request_peers(self):
        """
        Refresh the list of peers knew by this node
        """
        for endpoint in [e for e in self.node.endpoints if isinstance(e, BMAEndpoint)]:
            try:
                peers_data = await self.safe_request(endpoint, bma.network.peers,
                                                     req_args={'leaves': 'true'},
                                                     proxy=self._user_parameters.proxy())
                if not peers_data:
                    continue
                self.node.state = Node.ONLINE
                if peers_data['root'] != self.node.merkle_peers_root:
                    leaves = [leaf for leaf in peers_data['leaves']
                              if leaf not in self.node.merkle_peers_leaves]
                    for leaf_hash in leaves:
                        try:
                            leaf_data = await self.safe_request(endpoint,
                                                                bma.network.peers,
                                                                proxy=self._user_parameters.proxy(),
                                                                req_args={'leaf': leaf_hash})
                            if not leaf_data:
                                break
                            self.refresh_peer_data(leaf_data['leaf']['value'])
                        except (AttributeError, ValueError) as e:
                            self._logger.debug("Incorrect peer data in {leaf} : {err}".format(leaf=leaf_hash, err=str(e)))
                            self.change_state_and_emit(Node.OFFLINE)
                        except errors.DuniterError as e:
                            if e.ucode == 2012:
                                # Since with multinodes, peers or not the same on all nodes, sometimes this request results
                                # in peer not found error
                                self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
                            else:
                                self.change_state_and_emit(Node.OFFLINE)
                                self._logger.debug("Incorrect peer data in {leaf} : {err}".format(leaf=leaf_hash, err=str(e)))
                    else:
                        self.node.merkle_peers_root = peers_data['root']
                        self.node.merkle_peers_leaves = tuple(peers_data['leaves'])
                return  # Break endpoints loop
            except errors.DuniterError as e:
                self._logger.debug("Error in peers reply : {0}".format(str(e)))
                self.change_state_and_emit(Node.OFFLINE)
        else:
            if self.session.closed:
                pass
            else:
                self._logger.debug("Could not connect to any BMA endpoint")
                self.change_state_and_emit(Node.OFFLINE)

    def refresh_peer_data(self, peer_data):
        if "raw" in peer_data:
            try:
                str_doc = "{0}{1}\n".format(peer_data['raw'],
                                            peer_data['signature'])
                peer_doc = Peer.from_signed_raw(str_doc)
                self.neighbour_found.emit(peer_doc)
            except MalformedDocumentError as e:
                self._logger.debug("{:}:{:}".format(str(e.__class__.__name__), str(e)))
        else:
            self._logger.debug("Incorrect leaf reply")

    def change_state_and_emit(self, new_state):
        if self.node.state != new_state:
            self._logger.debug("Changing state {0} > {1}".format(self.node.state, new_state))
            self.node.last_state_change = time.time()
            self.node.state = new_state
            self.changed.emit()
