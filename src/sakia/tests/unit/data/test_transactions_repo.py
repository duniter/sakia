from sakia.data.repositories import TransactionsRepo, SakiaDatabase
from sakia.data.entities import Transaction
from duniterpy.documents import BlockUID
import unittest
import sqlite3


class TestTransactionsRepo(unittest.TestCase):
    def setUp(self):
        sqlite3.register_adapter(BlockUID, str)
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        self.meta_repo = SakiaDatabase(sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES))

    def tearDown(self):
        self.con.close()

    def test_add_get_drop_transaction(self):
        meta_repo = SakiaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        transactions_repo = TransactionsRepo(self.con)
        transactions_repo.insert(Transaction("testcurrency",
                                           "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                                           "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           1473108382,
                                           "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                           "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                           1565,
                                           1,
                                           "",
                                           0))
        transaction = transactions_repo.get_one(sha_hash="FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
        self.assertEqual(transaction.currency, "testcurrency")
        self.assertEqual(transaction.sha_hash, "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
        self.assertEqual(transaction.written_on.number, 20)
        self.assertEqual(transaction.written_on.sha_hash, "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
        self.assertEqual(transaction.blockstamp.number, 15)
        self.assertEqual(transaction.blockstamp.sha_hash, "76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67")
        self.assertEqual(transaction.timestamp, 1473108382)
        self.assertEqual(transaction.signature, "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==")
        self.assertEqual(transaction.amount, 1565)
        self.assertEqual(transaction.amount_base, 1)
        self.assertEqual(transaction.issuer, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(transaction.receiver, "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
        self.assertEqual(transaction.comment, "")
        self.assertEqual(transaction.txid, 0)

        transactions_repo.drop(transaction)
        transaction = transactions_repo.get_one(sha_hash="FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
        self.assertIsNone(transaction)

    def test_add_get_multiple_transaction(self):
        meta_repo = SakiaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        transactions_repo = TransactionsRepo(self.con)
        transactions_repo.insert(Transaction("testcurrency",
                                           "A0AC57E2E4B24D66F2D25E66D8501D8E881D9E6453D1789ED753D7D426537ED5",
                                           "12-AAEFCCE0E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           "543-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           1473108382,
                                           "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                           "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                           "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           14,
                                           2,
                                           "Test",
                                           2))
        transactions_repo.insert(Transaction("testcurrency",
                                           "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                                           "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           1473108382,
                                           "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                           "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                           1565,
                                           1,
                                           "",
                                           0))
        transactions = transactions_repo.get_all(currency="testcurrency")
        self.assertIn("testcurrency", [t.currency for t in transactions])
        self.assertIn("7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", [t.receiver for t in transactions])
        self.assertIn("FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn", [t.issuer for t in transactions])

    def test_add_update_transaction(self):
        meta_repo = SakiaDatabase(self.con)
        meta_repo.prepare()
        meta_repo.upgrade_database()
        transactions_repo = TransactionsRepo(self.con)
        transaction = Transaction("testcurrency",
                                           "FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365",
                                           "20-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           "15-76543400E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                           1473108382,
                                           "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
                                           "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn",
                                           1565,
                                           1,
                                           "",
                                           0)
        transactions_repo.insert(transaction)
        transaction.written_on = None
        transactions_repo.update(transaction)
        transaction2 = transactions_repo.get_one(sha_hash="FCAD5A388AC8A811B45A9334A375585E77071AA9F6E5B6896582961A6C66F365")
        self.assertEqual(transaction2.written_on, BlockUID.empty())
