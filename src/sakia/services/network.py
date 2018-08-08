import asyncio
import logging
import time
import random

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt
from duniterpy.api import errors
from duniterpy.documents import MalformedDocumentError
from duniterpy.documents.ws2p.heads import *
from duniterpy.documents.peer import BMAEndpoint
from duniterpy.key import VerifyingKey
from sakia.data.connectors import NodeConnector
from sakia.data.entities import Node
from sakia.decorators import asyncify
from sakia.errors import InvalidNodeCurrency


class NetworkService(QObject):
    """
    A network is managing nodes polling and crawling of a
    given community.
    """
    node_changed = pyqtSignal(Node)
    new_node_found = pyqtSignal(Node)
    node_removed = pyqtSignal(Node)
    latest_block_changed = pyqtSignal(BlockUID)
    root_nodes_changed = pyqtSignal()

    def __init__(self, app, currency, node_processor, connectors, blockchain_service, identities_service):
        """
        Constructor of a network

        :param sakia.app.Application app: The application
        :param str currency: The currency name of the community
        :param sakia.data.processors.NodesProcessor node_processor: the nodes processor for given currency
        :param list connectors: The connectors to nodes of the network
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        """
        super().__init__()
        self._app = app
        self._logger = logging.getLogger('sakia')
        self._processor = node_processor
        self._connectors = []
        for c in connectors:
            self.add_connector(c)
        self.currency = currency
        self._must_crawl = False
        self._ws2p_heads_refreshing = False
        self._block_found = self._processor.current_buid(self.currency)
        self._discovery_stack = []
        self._blockchain_service = blockchain_service
        self._identities_service = identities_service
        self._discovery_loop_task = None

    @classmethod
    def create(cls, node_processor, node_connector):
        """
        Create a new network with one knew node
        Crawls the nodes from the first node to build the
        community network

        :param sakia.data.processors.NodeProcessor node_processor: The nodes processor
        :param sakia.data.connectors.NodeConnector node_connector: The first connector of the network service
        :return:
        """
        connectors = [node_connector]
        node_processor.insert_node(node_connector.node)
        network = cls(node_connector.node.currency, node_processor, connectors, node_connector.session)
        return network

    @classmethod
    def load(cls, app, currency, node_processor, blockchain_service, identities_service):
        """
        Create a new network with all known nodes

        :param sakia.app.Application app: Sakia application
        :param str currency: The currency of this service
        :param sakia.data.processors.NodeProcessor node_processor: The nodes processor
        :return:
        """

        connectors = []
        sample = []
        for n in node_processor.online_nodes(currency):
            for e in n.endpoints:
                if isinstance(e, BMAEndpoint):
                    sample.append(n)
                    continue

        for node in random.sample(sample, min(len(sample), 6)):
            connectors.append(NodeConnector(node, app.parameters))
        network = cls(app, currency, node_processor, connectors, blockchain_service, identities_service)
        return network

    def start_coroutines(self):
        """
        Start network nodes crawling
        :return:
        """
        if not self._discovery_loop_task:
            self._discovery_loop_task = asyncio.ensure_future(self.discover_network())

    def nodes(self):
        """
        Get all nodes
        :return:
        """
        return self._processor.nodes(self.currency)

    def commit_node(self, node):
        self._processor.commit_node(node)

    def current_buid(self):
        return self._processor.current_buid(self.currency)

    async def stop_coroutines(self, closing=False):
        """
        Stop network nodes crawling.
        """
        self._must_crawl = False
        close_tasks = []
        self._logger.debug("Start closing")
        for connector in self._connectors:
            close_tasks.append(asyncio.ensure_future(connector.close_ws()))
        self._logger.debug("Closing {0} websockets".format(len(close_tasks)))
        if len(close_tasks) > 0:
            await asyncio.wait(close_tasks, timeout=15)
        self._logger.debug("Closed")

    def continue_crawling(self):
        return self._must_crawl

    def add_connector(self, node_connector):
        """
        Add a nod to the network.
        """
        self._connectors.append(node_connector)
        node_connector.block_found.connect(self.handle_new_block, type=Qt.UniqueConnection|Qt.QueuedConnection)
        node_connector.changed.connect(self.handle_change, type=Qt.UniqueConnection|Qt.QueuedConnection)
        node_connector.identity_changed.connect(self.handle_identity_change, type=Qt.UniqueConnection|Qt.QueuedConnection)
        node_connector.neighbour_found.connect(self.handle_new_node, type=Qt.UniqueConnection|Qt.QueuedConnection)
        self._logger.debug("{:} connected".format(node_connector.node.pubkey[:5]))

    @asyncify
    async def refresh_once(self):
        for connector in self._connectors:
            await asyncio.sleep(1)
            await connector.init_session()
            connector.refresh(manual=True)

    async def discover_network(self):
        """
        Start crawling which never stops.
        To stop this crawling, call "stop_crawling" method.
        """
        self._must_crawl = True
        first_loop = True
        asyncio.ensure_future(self.discovery_loop())
        self.refresh_once()
        while self.continue_crawling():
            if not first_loop:
                for node in self._processor.nodes(self.currency):
                    if node.state > Node.FAILURE_THRESHOLD and node.last_state_change + 3600 < time.time():
                        for connector in self._connectors:
                            if connector.node.pubkey == node.pubkey:
                                await connector.close_ws()
                                connector.disconnect()
                                self._connectors.remove(connector)
                        self._processor.delete_node(connector.node)
                        self.node_removed.emit(connector.node)
                    if len(self._connectors) < 6:
                        sample = []
                        for n in self._processor.online_nodes(self.currency):
                            for e in n.endpoints:
                                if isinstance(e, BMAEndpoint):
                                    sample.append(n)
                                    continue

                        for node in random.sample(sample, min(len(sample), 1)):
                            self.add_connector(NodeConnector(node, self.app.parameters))


                self.run_ws2p_check()
            first_loop = False
            await asyncio.sleep(15)

        self._logger.debug("End of network discovery")

    async def discovery_loop(self):
        """
        Handle poping of nodes in discovery stack
        :return:
        """
        while self.continue_crawling():
            try:
                await asyncio.sleep(1)
                peer = self._discovery_stack.pop()
            except IndexError:
                await asyncio.sleep(2)
            else:
                node, updated = self._processor.update_peer(self.currency, peer)
                if not node:
                    self._logger.debug("New node found : {0}".format(peer.pubkey[:5]))
                    try:
                        connector = NodeConnector.from_peer(self.currency, peer, self._app.parameters)
                        node = connector.node
                        self._processor.insert_node(connector.node)
                        self.new_node_found.emit(node)
                    except InvalidNodeCurrency as e:
                        self._logger.debug(str(e))
                if self._blockchain_service.initialized():
                    self._processor.handle_success(node)
                    try:
                        identity = await self._identities_service.find_from_pubkey(node.pubkey)
                        identity = await self._identities_service.load_requirements(identity)
                        node.member = identity.member
                        node.uid = identity.uid
                        self._processor.update_node(node)
                        self.node_changed.emit(node)
                    except errors.DuniterError as e:
                        self._logger.error(e.message)

    def handle_new_node(self, peer):
        key = VerifyingKey(peer.pubkey)
        if key.verify_document(peer):
            if len(self._discovery_stack) < 1000 \
               and peer.blockUID.number + 2400 > self.current_buid().number \
               and peer.signatures not in [p.signatures[0] for p in self._discovery_stack]:
                self._logger.debug("Stacking new peer document : {0}".format(peer.pubkey))
                self._discovery_stack.append(peer)
        else:
            self._logger.debug("Wrong document received : {0}".format(peer.signed_raw()))

    @pyqtSlot()
    def handle_identity_change(self):
        connector = self.sender()
        self._processor.update_node(connector.node)
        self.node_changed.emit(connector.node)

    def handle_new_block(self, block_uid):
        if self.current_buid() != block_uid:
            self.run_ws2p_check()

    def run_ws2p_check(self):
        if not self._ws2p_heads_refreshing:
            self._ws2p_heads_refreshing = True
            asyncio.async(self.check_ws2p_heads())

    async def check_ws2p_heads(self):
        await asyncio.sleep(5)
        futures = []
        for connector in self._connectors:
            futures.append(connector.request_ws2p_heads())

        responses = await asyncio.gather(*futures, return_exceptions=True)

        ws2p_heads = {}
        for r in responses:
            if isinstance(r, errors.DuniterError):
                self._logger.debug("Exception in responses : " + str(r))
                continue
            elif isinstance(r, BaseException):
                self._logger.debug("Exception in responses : " + str(r))
            else:
                if r:
                    for head_data in r["heads"]:
                        try:
                            if "messageV2" in head_data:
                                head, _ = HeadV2.from_inline(head_data["messageV2"], head_data["sigV2"])
                            else:
                                head, _ = HeadV1.from_inline(head_data["message"], head_data["sig"])

                            VerifyingKey(head.pubkey).verify_ws2p_head(head)
                            if head.pubkey in ws2p_heads:
                                if ws2p_heads[head.pubkey].blockstamp < head.blockstamp:
                                    ws2p_heads[head.pubkey] = head
                            else:
                                ws2p_heads[head.pubkey] = head
                        except MalformedDocumentError as e:
                            self._logger.error(str(e))

        for head in ws2p_heads.values():
            node, updated = self._processor.update_ws2p(self.currency, head)
            if node and updated:
                self.node_changed.emit(node)

        self._ws2p_heads_refreshing = False

        current_buid = self._processor.current_buid(self.currency)
        self._logger.debug("{0} -> {1}".format(self._block_found.sha_hash[:10], current_buid.sha_hash[:10]))
        if self._block_found.sha_hash != current_buid.sha_hash:
            self._logger.debug("Latest block changed : {0}".format(current_buid.number))
            self.latest_block_changed.emit(current_buid)
            self._logger.debug("Start refresh")
            self._block_found = current_buid
            asyncio.ensure_future(self._blockchain_service.handle_blockchain_progress(self._block_found))

    def handle_change(self):
        node_connector = self.sender()
        self._processor.update_node(node_connector.node)
        self.node_changed.emit(node_connector.node)

    def handle_success(self):
        node_connector = self.sender()
        self._processor.handle_success(node_connector.node)
        self.changed.emit()

    def handle_failure(self, weight=1):
        node_connector = self.sender()
        self._processor.handle_failure(node_connector.node, weight)
        self.changed.emit()
