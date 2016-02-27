import unittest
from asynctest import Mock, MagicMock, CoroutineMock
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import IdentitiesRegistry, Identity
from sakia.core import Account
from sakia.tests import QuamashTest
from ucoinpy.documents import BlockUID, SelfCertification


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

    def test_send_membership(self):
        account = Account("test_salt", "H8uYXvyF6GWeCr8cwFJ6V5B8tNprwRdjepFNJBqivrzr",
                          "test_account", [], [], [],
                          self.identities_registry)
        account_identity = MagicMock(autospec='sakia.core.registry.Identity')
        account_identity.selfcert = CoroutineMock(return_value=SelfCertification(2, "meta_brouzouf",
                                            "H8uYXvyF6GWeCr8cwFJ6V5B8tNprwRdjepFNJBqivrzr", "test_account", 1000000000, ""))
        community = MagicMock(autospec='sakia.core.Community')
        community.blockUID = CoroutineMock(return_value=BlockUID(3102, "0000C5336F0B64BFB87FF4BC858AE25726B88175"))
        self.identities_registry.future_find = CoroutineMock(return_value=account_identity)
        community.bma_access = MagicMock(autospec='sakia.core.net.api.bma.access.BmaAccess')
        response = Mock()
        response.json = CoroutineMock(return_value={
  "signature": "H41/8OGV2W4CLKbE35kk5t1HJQsb3jEM0/QGLUf80CwJvGZf3HvVCcNtHPUFoUBKEDQO9mPK3KJkqOoxHpqHCw==",
  "membership": {
    "version": 2,
    "currency": "beta_brouzouf",
    "issuer": "HsLShAtzXTVxeUtQd7yi5Z5Zh4zNvbu8sTEZ53nfKcqY",
    "membership": "IN",
    "sigDate": 1390739944,
    "uid": "superman63"
  }
})
        response.status = 200
        community.bma_access.broadcast = CoroutineMock(return_value=[response])
        async def exec_test():
            result = await account.send_membership("test_password", community, "IN")
            self.assertTrue(result)

        self.lp.run_until_complete(exec_test())

    def test_send_certification(self):
        cert_signal_sent = False
        def check_certification_accepted():
            nonlocal cert_signal_sent
            cert_signal_sent = True

        account = Account("test_salt", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                          "test_account", [], [], [],
                          self.identities_registry)
        account.certification_accepted.connect(check_certification_accepted)
        account_identity = MagicMock(autospec='sakia.core.registry.Identity')
        account_identity.selfcert = CoroutineMock(return_value=SelfCertification(2, "meta_brouzouf",
                                            "H8uYXvyF6GWeCr8cwFJ6V5B8tNprwRdjepFNJBqivrzr", "test_account",
                                            BlockUID(1000, "49E2A1D1131F1496FAD6EDAE794A9ADBFA8844029675E3732D3B027ABB780243"),
                                            "82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw=="))

        certified = MagicMock(autospec='sakia.core.registry.Identity')
        certified.uid = "john"
        certified.pubkey = "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ"
        certified.sigdate = 1441130831
        certified.selfcert = CoroutineMock(return_value=SelfCertification(2, "meta_brouzouf",
                                            "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ", "john",
                                            BlockUID(1200, "49E2A1D1131F1496FAD6EDAE794A9ADBFA8844029675E3732D3B027ABB780243"),
                                            "82o1sNCh1bLpUXU6nacbK48HBcA9Eu2sPkL1/3c2GtDPxBUZd2U2sb7DxwJ54n6ce9G0Oy7nd1hCxN3fS0oADw=="))

        community = MagicMock(autospec='sakia.core.Community')
        community.blockUID = CoroutineMock(return_value=BlockUID(3102, "49E2A1D1131F1496FAD6EDAE794A9ADBFA8844029675E3732D3B027ABB780243"))
        self.identities_registry.future_find = CoroutineMock(side_effect=lambda pubkey, community :account_identity \
                        if pubkey == "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ" else certified)
        community.bma_access = MagicMock(autospec='sakia.core.net.api.bma.access.BmaAccess')
        response = Mock()
        response.json = CoroutineMock(return_value={})
        response.status = 200
        community.bma_access.broadcast = CoroutineMock(return_value=[response])
        async def exec_test():
            result = await account.certify("test_password", community, "")
            self.assertTrue(result)

        self.lp.run_until_complete(exec_test())
        self.assertTrue(cert_signal_sent)



