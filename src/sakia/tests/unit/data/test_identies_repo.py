from sakia.data.repositories import IdentitiesRepo, MetaDatabase
from sakia.data.entities import Identity
from duniterpy.documents import BlockUID
import unittest
import sqlite3


class TestIdentitiesRepo(unittest.TestCase):
    def setUp(self):
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.con = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES)

    def tearDown(self):
        self.con.close()

    def test_add_get_identity(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        identities_repo = IdentitiesRepo(self.con)
        identities_repo.insert(Identity("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                        "john",
                                        "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                        "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                        1473108382,
                                        False,
                                        None,
                                        0))
        identity = identities_repo.get_one("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(identity.currency, "testcurrency")
        self.assertEqual(identity.pubkey, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(identity.uid, "john")
        self.assertEqual(identity.blockstamp.number, 20)
        self.assertEqual(identity.blockstamp.sha_hash, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
        self.assertEqual(identity.timestamp, 1473108382)
        self.assertEqual(identity.signature, "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==")
        self.assertEqual(identity.member, False)
        self.assertEqual(identity.membership_buid, BlockUID.empty())
        self.assertEqual(identity.membership_timestamp, 0)
        identities_repo.drop("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        identity = identities_repo.get_one("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertIsNone(identity)




