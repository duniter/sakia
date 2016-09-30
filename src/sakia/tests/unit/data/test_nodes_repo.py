from sakia.data.repositories import NodesRepo, MetaDatabase
from sakia.data.entities import Node
from duniterpy.documents import BlockUID, BMAEndpoint, UnknownEndpoint, block_uid
import unittest
import sqlite3


class TestNodesRepo(unittest.TestCase):
    def setUp(self):
        self.meta_repo = MetaDatabase.create(":memory:")
        self.meta_repo.prepare()
        self.meta_repo.upgrade_database()

    def tearDown(self):
        pass

    def test_add_get_drop_node(self):
        nodes_repo = NodesRepo(self.meta_repo.conn)
        inserted = Node("testcurrency",
             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
             """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
             BlockUID.empty(),
            "doe",
             "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
             "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
             Node.ONLINE,
             "duniter",
             "0.30.17")
        nodes_repo.insert(inserted)
        node = nodes_repo.get_one(currency="testcurrency",
                                  pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(node.currency, "testcurrency")
        self.assertEqual(node.pubkey, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(node.endpoints[0], BMAEndpoint("test-net.duniter.fr", "13.222.11.22", None, 9201))
        self.assertEqual(node.endpoints[1], BMAEndpoint("testnet.duniter.org", None, None, 80))
        self.assertEqual(node.endpoints[2], UnknownEndpoint("UNKNOWNAPI", ["some", "useless", "information"]))
        self.assertEqual(node.previous_buid, block_uid("14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
        self.assertEqual(node.current_buid, block_uid("15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
        self.assertEqual(node.state, Node.ONLINE)
        self.assertEqual(node.software, "duniter")
        self.assertEqual(node.version, "0.30.17")
        self.assertEqual(node.merkle_peers_root, Node.MERKLE_EMPTY_ROOT)
        self.assertEqual(node.merkle_peers_leaves, tuple())

        nodes_repo.drop(node)
        node = nodes_repo.get_one(pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertIsNone(node)

    def test_add_get_multiple_node(self):
        nodes_repo = NodesRepo(self.meta_repo.conn)
        nodes_repo.insert(Node("testcurrency",
                               "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                               BlockUID.empty(),
                                "doe",
                               "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               Node.ONLINE,
                               "duniter",
                               "0.30.17"))
        nodes_repo.insert(Node("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               "BASIC_MERKLED_API test-net.duniter.org 22.22.22.22 9201",
                               BlockUID.empty(),
                                "doe",
                               "18-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               "12-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               Node.ONLINE,
                               "duniter",
                               "0.30.2a5"))
        nodes = nodes_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [t.currency for t in nodes])
        self.assertIn("7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", [n.pubkey for n in nodes])
        self.assertIn("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn", [n.pubkey for n in nodes])

    def test_add_update_node(self):
        nodes_repo = NodesRepo(self.meta_repo.conn)
        node = Node("testcurrency",
                       "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                       """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                       BlockUID.empty(),
                        "doe",
                       "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                       "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                       Node.ONLINE,
                       "duniter")
        nodes_repo.insert(node)
        node.previous_buid = node.current_buid
        node.current_buid = "16-77543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"
        nodes_repo.update(node)
        node2 = nodes_repo.get_one(pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(node2.current_buid, block_uid("16-77543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
        self.assertEqual(node2.previous_buid, block_uid("15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
