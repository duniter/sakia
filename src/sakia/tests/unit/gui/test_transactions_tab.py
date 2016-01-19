import unittest
from unittest.mock import patch, MagicMock, Mock
from asynctest.mock import CoroutineMock
from asynctest.mock import MagicMock as AsyncMagicMock
from PyQt5.QtCore import QLocale, pyqtSignal
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain
from sakia.gui.transactions_tab import TransactionsTabWidget, Ui_transactionsTabWidget, QWidget


class TestTransactionTab(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        self.identity = Mock(specs='core.registry.Identity')
        self.identity.pubkey = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        self.identity.uid = "A"

    def tearDown(self):
        self.tearDownQuamash()

    @patch('sakia.gen_resources.transactions_tab_uic.Ui_transactionsTabWidget', create=True)
    @patch('PyQt5.QtWidgets.QWidget', create=True)
    def test_view_in_wot(self, widget, view):
        wot_refreshed = False

        def refresh_wot(identity):
            nonlocal wot_refreshed
            self.assertEqual(identity, self.identity)
            wot_refreshed = True

        app = Mock('sakia.core.Application')
        async def exec_test():
            transaction_tab = TransactionsTabWidget(app, widget, view)
            transaction_tab.view_in_wot.connect(refresh_wot)
            transaction_tab.view_wot(self.identity)

        self.lp.run_until_complete(exec_test())
        self.assertTrue(wot_refreshed)

    @patch('sakia.gen_resources.transactions_tab_uic.Ui_transactionsTabWidget', create=True)
    @patch('PyQt5.QtWidgets.QWidget', create=True)
    def copy_pubkey_to_clipboard(self, widget, view):
        app = Mock('sakia.core.Application')
        async def exec_test():
            transaction_tab = TransactionsTabWidget(app, widget, view)
            transaction_tab.copy_pubkey_to_clipboard(self.identity)
        self.lp.run_until_complete(exec_test())
        self.assertEqual(self.qapplication.clipboard().text(), "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk")

    @patch('sakia.gen_resources.transactions_tab_uic.Ui_transactionsTabWidget', create=True)
    @patch('PyQt5.QtWidgets.QWidget', create=True)
    def test_copy_block_to_clipboard(self, widget, view):
        app = AsyncMagicMock('sakia.core.Application')
        community = Mock('sakia.core.Community')
        community.get_block = CoroutineMock(side_effect=lambda n: nice_blockchain.bma_blockchain_current if n == 15 \
                                                    else nice_blockchain.bma_blockchain_0)
        self.qapplication.clipboard().clear()
        async def exec_test():
            transaction_tab = TransactionsTabWidget(app, widget, view)
            transaction_tab.community = community
            transaction_tab.copy_block_to_clipboard(15)

        self.lp.run_until_complete(exec_test())
        raw_block = "{0}{1}\n".format(nice_blockchain.bma_blockchain_current["raw"],
                                      nice_blockchain.bma_blockchain_current["signature"])
        self.assertEqual(self.qapplication.clipboard().text(), raw_block)
