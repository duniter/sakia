import sys
import unittest
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.core import Account
from sakia.tests import QuamashTest


class TestAccount(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

    def tearDown(self):
        self.tearDownQuamash()

    def test_load_save_account(self):
        account = Account("test_salt", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                          "test_uid", [], [], [], self.identities_registry)
        json_data = account.jsonify()
        account_from_json = Account.load(json_data, self.identities_registry)

        self.assertEqual(account.name, account_from_json.name)
        self.assertEqual(account.pubkey, account_from_json.pubkey)
        self.assertEqual(len(account.communities), len(account_from_json.communities))
        self.assertEqual(len(account.wallets), len(account.wallets))

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
