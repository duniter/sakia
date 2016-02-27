import unittest
from unittest.mock import patch, MagicMock, Mock
from asynctest.mock import CoroutineMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from sakia.gui.widgets.context_menu import ContextMenu
from ucoinpy.documents import Membership, BlockUID
from sakia.tools.exceptions import MembershipNotFoundError


class TestContextMenu(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        self.identity = Mock(specs='sakia.core.registry.Identity')
        self.identity.pubkey = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        self.identity.uid = "A"

        self.app = MagicMock(specs='sakia.core.Application')
        self.account = MagicMock(specs='sakia.core.Account')
        self.community = MagicMock(specs='sakia.core.Community')
        self.password_asker = MagicMock(specs='sakia.gui.password_asker.PasswordAsker')

    def tearDown(self):
        self.tearDownQuamash()

    @patch('PyQt5.QtWidgets.QMenu', create=True)
    def test_view_in_wot(self, qmenu):
        wot_refreshed = False

        def refresh_wot(identity):
            nonlocal wot_refreshed
            self.assertEqual(identity, self.identity)
            wot_refreshed = True

        async def exec_test():
            context_menu = ContextMenu(qmenu, self.app, self.account, self.community, self.password_asker)
            context_menu.view_identity_in_wot.connect(refresh_wot)
            context_menu.view_wot(self.identity)

        self.lp.run_until_complete(exec_test())
        self.assertTrue(wot_refreshed)

    @patch('PyQt5.QtWidgets.QMenu', create=True)
    def test_copy_pubkey_to_clipboard(self, qmenu):
        app = Mock('sakia.core.Application')

        async def exec_test():
            context_menu = ContextMenu(qmenu, self.app, self.account, self.community, self.password_asker)
            context_menu.copy_pubkey_to_clipboard(self.identity)

        self.lp.run_until_complete(exec_test())
        self.assertEqual(self.qapplication.clipboard().text(), "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk")

    @patch('PyQt5.QtWidgets.QMenu', create=True)
    def test_copy_block_to_clipboard(self, qmenu):
        self.community.get_block = CoroutineMock(side_effect=lambda n: nice_blockchain.bma_blockchain_current if n == 15 \
            else nice_blockchain.bma_blockchain_0)
        self.qapplication.clipboard().clear()

        async def exec_test():
            context_menu = ContextMenu(qmenu, self.app, self.account, self.community, self.password_asker)
            context_menu.community = self.community
            context_menu.copy_block_to_clipboard(15)

        self.lp.run_until_complete(exec_test())
        raw_block = "{0}{1}\n".format(nice_blockchain.bma_blockchain_current["raw"],
                                      nice_blockchain.bma_blockchain_current["signature"])
        self.assertEqual(self.qapplication.clipboard().text(), raw_block)

    @patch('PyQt5.QtWidgets.QMenu', create=True)
    def test_copy_membership_to_clipboard(self, qmenu):
        ms_data = {
                    "version": 2,
                    "currency": "meta_brouzouf",
                    "membership": "IN",
                    "blockNumber": 49116,
                    "blockHash": "7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                    "written": 49119
                }
        ms_document = Membership(ms_data["version"], ms_data["currency"], self.identity.pubkey,
                                 BlockUID(ms_data["blockNumber"], ms_data["blockHash"]),
                                 ms_data["membership"], self.identity.uid, "49116-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67",
                                 "znWiWP7Sy9gg9pZq4YWKNpel8MM16VBM1lgBg2gWjSonnc+KVRCtQng5JB4JD0PgJJ0F8jdITuggFrRwqRfzAA==")
        self.identity.membership = CoroutineMock(return_value=ms_data)
        self.community.get_block = CoroutineMock(return_value={
  "version": 2,
  "nonce": 127424,
  "number": 49119,
  "powMin": 5,
  "time": 1453921638,
  "medianTime": 1453912797,
  "membersCount": 18,
  "monetaryMass": 14028534972234185000,
  "currency": "meta_brouzouf",
  "issuer": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
  "signature": "ZmjhoRubftJ/T2WYQ3gaDeTGGUJ3beUshtlWn1k/r5opk0vt48KG3w+9JU0T9YFR5uezllaek9efoNwAHRBLDw==",
  "hash": "49E2A1D1131F1496FAD6EDAE794A9ADBFA8844029675E3732D3B027ABB780243",
  "innerhash": "273DE1845F8A63677D69DD427E00DAD73D9AEDBA80356A2E0D2152939D9DAF0C",
  "parameters": "",
  "previousHash": "000005C27A1636FE07AB01766FBA060565142D79",
  "previousIssuer": "HBSSmqZjT4UQKsCntTSmZbu7iRP14HYtifLE6mW1PsBD",
  "dividend": None,
  "identities": [],
  "joiners": [
    "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:znWiWP7Sy9gg9pZq4YWKNpel8MM16VBM1lgBg2gWjSonnc+KVRCtQng5JB4JD0PgJJ0F8jdITuggFrRwqRfzAA==:49116-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67:49116-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67:A"
  ],
  "actives": [],
  "leavers": [],
  "excluded": [],
  "revoked": [],
  "certifications": [],
  "transactions": [],
  "raw": """Version: 2
Type: Block
Currency: meta_brouzouf
Number: 49119
PoWMin: 5
Time: 1453921638
MedianTime: 1453912797
Issuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk
PreviousHash: 000005C27A1636FE07AB01766FBA060565142D79
PreviousIssuer: HBSSmqZjT4UQKsCntTSmZbu7iRP14HYtifLE6mW1PsBD
MembersCount: 18
Identities:
Joiners:
HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:znWiWP7Sy9gg9pZq4YWKNpel8MM16VBM1lgBg2gWjSonnc+KVRCtQng5JB4JD0PgJJ0F8jdITuggFrRwqRfzAA==:49116-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67:49116-7518C700E78B56CC21FB1DDC6CBAB24E0FACC9A798F5ED8736EA007F38617D67:A
Actives:
Leavers:
Revoked:
Excluded:
Certifications:
Transactions:
InnerHash: 273DE1845F8A63677D69DD427E00DAD73D9AEDBA80356A2E0D2152939D9DAF0C
Nonce: 127424
"""
})
        self.qapplication.clipboard().clear()

        async def exec_test():
            context_menu = ContextMenu(qmenu, self.app, self.account, self.community, self.password_asker)
            context_menu.community = self.community
            context_menu.copy_membership_to_clipboard(self.identity)

        self.lp.run_until_complete(exec_test())
        self.assertEqual(self.qapplication.clipboard().text(), ms_document.signed_raw())

    @patch('PyQt5.QtWidgets.QMenu', create=True)
    def test_copy_membership_to_clipboard_not_found(self, qmenu):
        def raiser():
            raise MembershipNotFoundError("inso", "meta_brouzouf")
        self.identity.membership = CoroutineMock(side_effect=lambda c: raiser())

        self.qapplication.clipboard().clear()

        async def exec_test():
            context_menu = ContextMenu(qmenu, self.app, self.account, self.community, self.password_asker)
            context_menu.community = self.community
            context_menu.copy_membership_to_clipboard(self.identity)

        self.lp.run_until_complete(exec_test())
        self.assertEqual(self.qapplication.clipboard().text(), "")
