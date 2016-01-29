import unittest
from unittest.mock import patch, MagicMock, Mock
from asynctest.mock import CoroutineMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from sakia.gui.widgets.context_menu import ContextMenu
from ucoinpy.documents import Membership, BlockId
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
                    "version": 1,
                    "currency": "meta_brouzouf",
                    "membership": "IN",
                    "blockNumber": 49116,
                    "blockHash": "000004CA4F77E36CE52C23A9F2A8F2A259773CE9",
                    "written": 49119
                }
        ms_document = Membership(ms_data["version"], ms_data["currency"], self.identity.pubkey,
                                 BlockId(ms_data["blockNumber"], ms_data["blockHash"]),
                                 ms_data["membership"], self.identity.uid, 1421787800,
                                 "znWiWP7Sy9gg9pZq4YWKNpel8MM16VBM1lgBg2gWjSonnc+KVRCtQng5JB4JD0PgJJ0F8jdITuggFrRwqRfzAA==")
        self.identity.membership = CoroutineMock(return_value=ms_data)
        self.community.get_block = CoroutineMock(return_value={
  "version": 1,
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
  "hash": "0000075129361571E74380B686DE6E1E29FF8400",
  "parameters": "",
  "previousHash": "000005C27A1636FE07AB01766FBA060565142D79",
  "previousIssuer": "HBSSmqZjT4UQKsCntTSmZbu7iRP14HYtifLE6mW1PsBD",
  "dividend": None,
  "identities": [],
  "joiners": [
    "8Fi1VSTbjkXguwThF4v2ZxC5whK7pwG2vcGTkPUPjPGU:znWiWP7Sy9gg9pZq4YWKNpel8MM16VBM1lgBg2gWjSonnc+KVRCtQng5JB4JD0PgJJ0F8jdITuggFrRwqRfzAA==:49116:000004CA4F77E36CE52C23A9F2A8F2A259773CE9:1421787800:inso"
  ],
  "actives": [],
  "leavers": [],
  "excluded": [],
  "certifications": [],
  "transactions": [],
  "raw": "Version: 1\nType: Block\nCurrency: meta_brouzouf\nNonce: 127424\nNumber: 49119\nPoWMin: 5\nTime: 1453921638\nMedianTime: 1453912797\nIssuer: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nPreviousHash: 000005C27A1636FE07AB01766FBA060565142D79\nPreviousIssuer: HBSSmqZjT4UQKsCntTSmZbu7iRP14HYtifLE6mW1PsBD\nMembersCount: 18\nIdentities:\nJoiners:\nHnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk:znWiWP7Sy9gg9pZq4YWKNpel8MM16VBM1lgBg2gWjSonnc+KVRCtQng5JB4JD0PgJJ0F8jdITuggFrRwqRfzAA==:49116:000004CA4F77E36CE52C23A9F2A8F2A259773CE9:1421787800:A\nActives:\nLeavers:\nExcluded:\nCertifications:\nTransactions:\n"
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
