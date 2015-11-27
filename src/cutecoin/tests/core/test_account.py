import sys
import unittest
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from cutecoin.core.registry.identities import IdentitiesRegistry
from cutecoin.core import Account
from cutecoin.tests import get_application


class TestAccount(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)
        self.identities_registry = IdentitiesRegistry()

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

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
