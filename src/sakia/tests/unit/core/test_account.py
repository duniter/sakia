import unittest
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

    def test_add_contact(self):
        called = False

        def signal_called():
            nonlocal called
            called = True
        account = Account("test_salt", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                          "test_uid", [], [], [], self.identities_registry)
        account.contacts_changed.connect(signal_called)
        account.add_contact({"uid":"friend", "pubkey":"FFFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"})
        self.assertEqual(len(account.contacts), 1)
        self.assertEqual(account.contacts[0]["uid"], "friend")
        self.assertEqual(account.contacts[0]["pubkey"], "FFFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk")
        self.assertTrue(called)

    def test_remove_contact(self):
        called = False

        def signal_called():
            nonlocal called
            called = True
        contact = {"uid":"friend", "pubkey":"FFFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"}
        account = Account("test_salt", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                          "test_uid", [], [], [contact],
                          self.identities_registry)
        account.contacts_changed.connect(signal_called)
        account.remove_contact(contact)
        self.assertEqual(len(account.contacts), 0)
        self.assertTrue(called)

    def test_edit_contact(self):
        called = False

        def signal_called():
            nonlocal called
            called = True
        contact = {"uid":"friend", "pubkey":"FFFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"}
        account = Account("test_salt", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                          "test_uid", [], [], [contact],
                          self.identities_registry)
        account.contacts_changed.connect(signal_called)
        account.edit_contact(0, {"uid": "ennemy", "pubkey": "FFFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"})
        self.assertEqual(len(account.contacts), 1)
        self.assertEqual(account.contacts[0]["uid"], "ennemy")
        self.assertEqual(account.contacts[0]["pubkey"], "FFFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk")
        self.assertTrue(called)