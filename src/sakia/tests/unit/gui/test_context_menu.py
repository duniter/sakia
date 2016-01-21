import unittest
from unittest.mock import patch, MagicMock, Mock
from asynctest.mock import CoroutineMock
from asynctest.mock import MagicMock as AsyncMagicMock
from PyQt5.QtCore import QLocale, pyqtSignal
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from sakia.gui.widgets import ContextMenu


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
