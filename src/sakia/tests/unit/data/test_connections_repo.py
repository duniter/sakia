from sakia.data.repositories import ConnectionsRepo, MetaDatabase
from sakia.data.entities import Connection
from duniterpy.documents import BlockUID
import unittest
import sqlite3


class TestConnectionsRepo(unittest.TestCase):
    def setUp(self):
        self.meta_repo = MetaDatabase.create(":memory:")
        self.meta_repo.prepare()
        self.meta_repo.upgrade_database()

    def tearDown(self):
        pass

    def test_add_get_drop_connection(self):
        connections_repo = ConnectionsRepo(self.meta_repo.conn)
        connections_repo.insert(Connection("testcurrency",
                                                 "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                                 "somesalt"))
        connection = connections_repo.get_one(currency="testcurrency",
                                           pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           salt="somesalt")
        self.assertEqual(connection.currency, "testcurrency")
        self.assertEqual(connection.pubkey, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
        self.assertEqual(connection.salt, "somesalt")
        connections_repo.drop(connection)
        connection = connections_repo.get_one(currency="testcurrency",
                                           pubkey="7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                                           salt="somesalt")
        self.assertIsNone(connection)
