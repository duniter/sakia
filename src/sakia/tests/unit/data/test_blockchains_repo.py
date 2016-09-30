import sqlite3
import unittest

from duniterpy.documents import BlockUID

from sakia.data.entities import Blockchain, BlockchainParameters
from sakia.data.repositories import BlockchainsRepo, MetaDatabase


class TestBlockchainsRepo(unittest.TestCase):
    def setUp(self):
        self.meta_repo = MetaDatabase.create(":memory:")
        self.meta_repo.prepare()
        self.meta_repo.upgrade_database()

    def tearDown(self):
        pass

    def test_add_get_drop_blockchain(self):
        blockchains_repo = BlockchainsRepo(self.meta_repo.conn)
        blockchains_repo.insert(Blockchain(
            BlockchainParameters(
                0.1,
                86400,
                100000,
                10800,
                40,
                2629800,
                31557600,
                1,
                0.9,
                604800,
                5,
                12,
                300,
                25,
                10,
                0.66),
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
        self.assertEqual(blockchain.parameters, BlockchainParameters(
                0.1,
                86400,
                100000,
                10800,
                40,
                2629800,
                31557600,
                1,
                0.9,
                604800,
                5,
                12,
                300,
                25,
                10,
                0.66))
        self.assertEqual(blockchain.currency, "testcurrency")
        self.assertEqual(blockchain.current_buid, BlockUID(20,
                                                           "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
                         )
        self.assertEqual(blockchain.nb_members, 10)

        blockchains_repo.drop(blockchain)
        blockchain = blockchains_repo.get_one(currency="testcurrency")
        self.assertIsNone(blockchain)

    def test_add_get_multiple_blockchain(self):
        blockchains_repo = BlockchainsRepo(self.meta_repo.conn)
        blockchains_repo.insert(Blockchain(
            BlockchainParameters(
                0.1,
                86400,
                100000,
                10800,
                40,
                2629800,
                31557600,
                1,
                0.9,
                604800,
                5,
                12,
                300,
                25,
                10,
                0.66),
            "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            10,
            1000000,
            86400,
            100000,
            0,
            999999,
            "testcurrency"
        ))
        blockchains_repo.insert(Blockchain(
            BlockchainParameters(
                0.1,
                86400 * 365,
                100000,
                10800,
                40,
                2629800,
                31557600,
                1,
                0.9,
                604800,
                5,
                12,
                300,
                25,
                10,
                0.66),
            "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
            20,
            1000000,
            86400,
            100000,
            0,
            999999,
            "testcurrency2"
        ))

        blockchains = blockchains_repo.get_all()
        # result sorted by currency name by default
        self.assertEquals(86400, blockchains[0].parameters.dt)
        self.assertEquals("testcurrency", blockchains[0].currency)
        self.assertEquals(10, blockchains[0].nb_members)

        self.assertEquals(86400*365, blockchains[1].parameters.dt)
        self.assertEquals("testcurrency2", blockchains[1].currency)
        self.assertEquals(20, blockchains[1].nb_members)

    def test_add_update_blockchain(self):
        blockchains_repo = BlockchainsRepo(self.meta_repo.conn)
        blockchain = Blockchain(
            BlockchainParameters(
                0.1,
                86400,
                100000,
                10800,
                40,
                2629800,
                31557600,
                1,
                0.9,
                604800,
                5,
                12,
                300,
                25,
                10,
                0.66),
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
