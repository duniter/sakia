from sakia.data.repositories import NodesRepo, MetaDatabase
from sakia.data.entities import Node
from duniterpy.documents import BlockUID, BMAEndpoint, UnknownEndpoint, block_uid
import unittest
import sqlite3


class TestNodesRepo(unittest.TestCase):
    def setUp(self):
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    def tearDown(self):
        self.con.close()

    def test_add_get_drop_node(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        nodes_repo = NodesRepo(self.con)
        nodes_repo.insert(Node("testcurrency",
                               "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                               "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               Node.ONLINE,
                               "duniter",
                               "0.30.17",
                               {}))
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
        self.assertEqual(node.merkle_nodes, {})

        nodes_repo.drop(node)
        node = nodes_repo.get_one(pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertIsNone(node)

    def test_add_get_multiple_node(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        nodes_repo = NodesRepo(self.con)
        nodes_repo.insert(Node("testcurrency",
                               "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                               "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               Node.ONLINE,
                               "duniter",
                               "0.30.17",
                               {}))
        nodes_repo.insert(Node("testcurrency",
                               "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                               "BASIC_MERKLED_API test-net.duniter.org 22.22.22.22 9201",
                               "18-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               "12-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                               Node.ONLINE,
                               "duniter",
                               "0.30.2a5",
                               {}))
        nodes = nodes_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [t.currency for t in nodes])
        self.assertIn("7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", [n.pubkey for n in nodes])
        self.assertIn("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn", [n.pubkey for n in nodes])

    def test_add_update_node(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        nodes_repo = NodesRepo(self.con)
        node = Node("testcurrency",
                       "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                       """BASIC_MERKLED_API test-net.duniter.fr 13.222.11.22 9201
BASIC_MERKLED_API testnet.duniter.org 80
UNKNOWNAPI some useless information""",
                       "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                       "14-AEFFCB00E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                       Node.ONLINE,
                       "duniter",
                       "0.30.17", {})
        nodes_repo.insert(node)
        node.previous_buid = node.current_buid
        node.current_buid = "16-77543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"
        nodes_repo.update(node)
        node2 = nodes_repo.get_one(pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(node2.current_buid, block_uid("16-77543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
        self.assertEqual(node2.previous_buid, block_uid("15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67"))
