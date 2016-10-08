import asyncio
import unittest
import sqlite3
import aiohttp
from duniterpy.documents import BlockUID, Peer
from sakia.tests import QuamashTest
from sakia.services import NetworkService
from sakia.data.connectors import NodeConnector
from sakia.data.repositories import NodesRepo, SakiaDatabase
from sakia.data.processors import NodesProcessor


class TestNetworkService(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_adapter(list, lambda ls: '\n'.join([str(v) for v in ls]))
        sqlite3.register_adapter(tuple, lambda ls: '\n'.join([str(v) for v in ls]))
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    def tearDown(self):
        self.tearDownQuamash()

    def test_network_discovering(self):
        meta_repo = SakiaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        nodes_repo = NodesRepo(self.con)

        async def exec_test():
            with aiohttp.ClientSession() as session:
                peering = await session.get("http://peer.duniter.org:8999/network/peering")
                self.assertEqual(peering.status, 200)
                data = await peering.json()
                peer_document = Peer.from_signed_raw("{0}{1}\n".format(data["raw"], data["signature"]))
                node_connector = NodeConnector.from_peer(peer_document.currency, peer_document, session)

                processor = NodesProcessor(peer_document.currency, nodes_repo)
                network_service = NetworkService.create(processor, node_connector)

                network_service._must_crawl = True
                asyncio.ensure_future(network_service.discovery_loop())
                network_service.refresh_once()
                await asyncio.sleep(20)
                self.assertGreater(len(processor.nodes()), 1)
                await asyncio.sleep(20)
                self.assertGreater(len(processor.nodes()), 2)
                await network_service.stop_coroutines(True)

        self.lp.run_until_complete(exec_test())
