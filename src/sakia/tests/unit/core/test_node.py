import unittest
from unittest.mock import Mock
from asynctest import CoroutineMock, patch
from duniterpy.documents import Peer, BlockUID
from PyQt5.QtCore import QLocale
from sakia.core.net import Node
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from pkg_resources import parse_version


class TestNode(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_from_peer(self):
        peer = Peer.from_signed_raw("""Version: 2
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API duniter.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""")
        node = Node.from_peer('meta_brouzouf', peer, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU", Mock("aiohttp.ClientSession"))
        self.assertEqual(node.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API duniter.inso.ovh 80")
        self.assertEqual(node.currency, "meta_brouzouf")

    @patch('duniterpy.api.bma.network.Peering')
    def test_from_address(self, peering):
        peering.return_value.get = CoroutineMock(return_value={
            "version": 2,
            "currency": "meta_brouzouf",
            "endpoints": [
                "BASIC_MERKLED_API duniter.inso.ovh 80"
            ],
            "block": "48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8",
            "signature": "82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==",
            "raw": "Version: 2\nType: Peer\nCurrency: meta_brouzouf\nPublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU\nBlock: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8\nEndpoints:\nBASIC_MERKLED_API duniter.inso.ovh 80\n",
            "pubkey": "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
        })

        async def exec_test():
            node = await Node.from_address("meta_brouzouf", "127.0.0.1", 9000, Mock("aiohttp.ClientSession"))
            self.assertEqual(node.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
            self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API duniter.inso.ovh 80")
            self.assertEqual(node.currency, "meta_brouzouf")

        self.lp.run_until_complete(exec_test())

    def test_from_json_to_json(self):
        json_data = {"version": "0.12.0", "state": 1, "fork_window": 0, "uid": "inso",
                      "block": nice_blockchain.bma_blockchain_current,
                      "peer": """Version: 2
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API duniter.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""",
                      "pubkey": "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU",
                      "last_change": 1448199706.6561477, "software": "duniter"}
        node = Node.from_json("meta_brouzouf", json_data, parse_version('0.12.0'), Mock("aiohttp.ClientSession"))
        self.assertEqual(node.version, "0.12.0")
        self.assertEqual(node.state, 1)
        self.assertEqual(node.fork_window, 0)
        self.assertEqual(node.uid, "inso")
        self.assertEqual(node.block, nice_blockchain.bma_blockchain_current)
        self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API duniter.inso.ovh 80")
        self.assertEqual(node.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(node.last_change, 1448199706.6561477)
        self.assertEqual(node.currency, "meta_brouzouf")
        self.assertEqual(node.peer.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(node.peer.blockUID.number, 48698)
        self.assertEqual(node.peer.blockUID.sha_hash, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8")

        result = node.jsonify()
        for key in result:
            self.assertEqual(result[key], json_data[key], "Error with key {0}".format(key))

    def test_jsonify_root_node(self):
        peer = Peer.from_signed_raw("""Version: 2
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API duniter.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""")
        node = Node(peer, "inso", "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU", nice_blockchain.bma_blockchain_current,
                 Node.ONLINE, 1111111111, {}, "duniter", "0.12", 0, Mock("aiohttp.ClientSession"))
        result = node.jsonify_root_node()
        self.assertEqual(result['pubkey'], "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(result['uid'], "inso")
        self.assertEqual(result['peer'], peer.signed_raw())