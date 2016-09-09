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

    def test_add_get_drop_identity(self):
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
                                        False,
                                        False,
                                        None,
                                        0))
        identity = identities_repo.get_one(currency="testcurrency",
                                           pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           uid="john",
                                           blockstamp=BlockUID(20,
                                                    "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
                                           )
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
        identities_repo.drop(identity)
        identity = identities_repo.get_one(currency="testcurrency",
                                           pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           uid="john",
                                           blockstamp=BlockUID(20,
                                                    "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
                                            )
        self.assertIsNone(identity)

    def test_add_get_multiple_identity(self):
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
                                        False,
                                        False,
                                        None,
                                        0))
        identities_repo.insert(Identity("testcurrency", "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                        "doe",
                                        "101-BAD49448A1AD73C978CEDCB8F137D20A5715EBAA739DAEF76B1E28EE67B2C00C",
                                        "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                        1455433535,
                                        False,
                                        False,
                                        False,
                                        None,
                                        0))
        identities = identities_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [i.currency for i in identities])
        self.assertIn("john", [i.uid for i in identities])
        self.assertIn("doe", [i.uid for i in identities])

    def test_add_update_identity(self):
        meta_repo = MetaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        identities_repo = IdentitiesRepo(self.con)
        identity = Identity("testcurrency", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                        "john",
                                        "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                        "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                        1473108382,
                                        False,
                                        False,
                                        False,
                                        None,
                                        0)
        identities_repo.insert(identity)
        identity.member = True
        identities_repo.update(identity)
        identity2 = identities_repo.get_one(currency="testcurrency",
                                            pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertTrue(identity2.member)
