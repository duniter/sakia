import sqlite3
import unittest

from duniterpy.documents import BlockUID

from sakia.data.entities import Blockchain
from sakia.data.repositories import BlockchainsRepo, MetaDatabase


class TestBlockchainsRepo(unittest.TestCase):
    def setUp(self):
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    def tearDown(self):
        self.con.close()

    def test_add_get_drop_blockchain(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        blockchains_repo = BlockchainsRepo(self.con)
        blockchains_repo.insert(Blockchain(
            "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            10,
            1000000,
            86400,
            100000,
            0,
            999999,
            "testcurrency"
        ))
        blockchain = blockchains_repo.get_one(currency="testcurrency")
        self.assertEqual(blockchain.currency, "testcurrency")
        self.assertEqual(blockchain.current_buid, BlockUID(20,
                                                           "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
                         )
        self.assertEqual(blockchain.nb_members, 10)

        blockchains_repo.drop(blockchain)
        blockchain = blockchains_repo.get_one(currency="testcurrency")
        self.assertIsNone(blockchain)

    def test_add_get_multiple_blockchain(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        blockchains_repo = BlockchainsRepo(self.con)
        blockchains_repo.insert(Blockchain(
            "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            10,
            1000000,
            86400,
            100000,
            0,
            999999,
            "testcurrency"
        )
        )
        blockchains_repo.insert(Blockchain(
            "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            20,
            1000000,
            86400,
            100000,
            0,
            999999,
            "testcurrency2"
        )
        )

        blockchains = blockchains_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [i.currency for i in blockchains])
        self.assertIn("testcurrency2", [i.currency for i in blockchains])
        self.assertIn(10, [i.nb_members for i in blockchains])
        self.assertIn(20, [i.nb_members for i in blockchains])

    def test_add_update_blockchain(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        blockchains_repo = BlockchainsRepo(self.con)
        blockchain = Blockchain(
            "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            10,
            1000000,
            86400,
            100000,
            0,
            999999,
            "testcurrency"
        )
        blockchains_repo.insert(blockchain)
        blockchain.nb_members = 30
        blockchains_repo.update(blockchain)
        blockchain2 = blockchains_repo.get_one(currency="testcurrency")
        self.assertEquals(30, blockchain2.nb_members)
