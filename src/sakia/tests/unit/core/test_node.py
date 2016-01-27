import unittest
from asynctest import CoroutineMock, patch
from ucoinpy.documents import Peer, BlockId
from PyQt5.QtCore import QLocale
from sakia.core.net import Node
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from distutils.version import StrictVersion


class TestNode(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

    def tearDown(self):
        self.tearDownQuamash()

    def test_from_peer(self):
        peer = Peer.from_signed_raw("""Version: 1
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API ucoin.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""")
        node = Node.from_peer('meta_brouzouf', peer, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(node.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API ucoin.inso.ovh 80")
        self.assertEqual(node.currency, "meta_brouzouf")

    @patch('ucoinpy.api.bma.network.Peering')
    def test_from_address(self, peering):
        peering.return_value.get = CoroutineMock(return_value={
            "version": 1,
            "currency": "meta_brouzouf",
            "endpoints": [
                "BASIC_MERKLED_API ucoin.inso.ovh 80"
            ],
            "block": "48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8",
            "signature": "82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==",
            "raw": "Version: 1\nType: Peer\nCurrency: meta_brouzouf\nPublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU\nBlock: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8\nEndpoints:\nBASIC_MERKLED_API ucoin.inso.ovh 80\n",
            "pubkey": "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU"
        })

        async def exec_test():
            node = await Node.from_address("meta_brouzouf", "127.0.0.1", 9000)
            self.assertEqual(node.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
            self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API ucoin.inso.ovh 80")
            self.assertEqual(node.currency, "meta_brouzouf")

        self.lp.run_until_complete(exec_test())

    def test_from_json_011(self):
        json_data = {"version": "0.12.0", "state": 1, "fork_window": 0, "uid": "cgeek",
                      "block": nice_blockchain.bma_blockchain_current,
                      "endpoints": ["BASIC_MERKLED_API metab.ucoin.io 88.174.120.187 9201"],
                      "pubkey": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                      "last_change": 1448199706.6561477, "currency": "meta_brouzouf", "sofware": "ucoin"}
        node = Node.from_json("meta_brouzouf", json_data, StrictVersion('0.11.5'))
        self.assertEqual(node.version, "0.12.0")
        self.assertEqual(node.state, 1)
        self.assertEqual(node.fork_window, 0)
        self.assertEqual(node.uid, "cgeek")
        self.assertEqual(node.block, nice_blockchain.bma_blockchain_current)
        self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API metab.ucoin.io 88.174.120.187 9201")
        self.assertEqual(node.pubkey, "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk")
        self.assertEqual(node.last_change, 1448199706.6561477)
        self.assertEqual(node.currency, "meta_brouzouf")
        self.assertEqual(node.peer.pubkey, "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk")
        self.assertEqual(BlockId.from_str(node.peer.blockid).number, 0)

    def test_from_json_to_json(self):
        json_data = {"version": "0.12.0", "state": 1, "fork_window": 0, "uid": "inso",
                      "block": nice_blockchain.bma_blockchain_current,
                      "peer": """Version: 1
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API ucoin.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""",
                      "pubkey": "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU",
                      "last_change": 1448199706.6561477, "software": "ucoin"}
        node = Node.from_json("meta_brouzouf", json_data, StrictVersion('0.12.0'))
        self.assertEqual(node.version, "0.12.0")
        self.assertEqual(node.state, 1)
        self.assertEqual(node.fork_window, 0)
        self.assertEqual(node.uid, "inso")
        self.assertEqual(node.block, nice_blockchain.bma_blockchain_current)
        self.assertEqual(node.endpoint.inline(), "BASIC_MERKLED_API ucoin.inso.ovh 80")
        self.assertEqual(node.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(node.last_change, 1448199706.6561477)
        self.assertEqual(node.currency, "meta_brouzouf")
        self.assertEqual(node.peer.pubkey, "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(BlockId.from_str(node.peer.blockid).number, 48698)
        self.assertEqual(BlockId.from_str(node.peer.blockid).sha_hash, "000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8")

        result = node.jsonify()
        for key in result:
            self.assertEqual(result[key], json_data[key], "Error with key {0}".format(key))

    def test_jsonify_root_node(self):
        peer = Peer.from_signed_raw("""Version: 1
Type: Peer
Currency: meta_brouzouf
PublicKey: 8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU
Block: 48698-000005E0F228038E4DDD4F6CA4ACB01EC88FBAF8
Endpoints:
BASIC_MERKLED_API ucoin.inso.ovh 80
82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw==
""")
        node = Node(peer, "inso", "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU", nice_blockchain.bma_blockchain_current,
                 Node.ONLINE, 1111111111, {}, "ucoin", "0.12", 0)
        result = node.jsonify_root_node()
        self.assertEqual(result['pubkey'], "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU")
        self.assertEqual(result['uid'], "inso")
        self.assertEqual(result['peer'], peer.signed_raw())