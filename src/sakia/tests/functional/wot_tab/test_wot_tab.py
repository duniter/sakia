import asyncio
import logging
import sys
import time
import unittest

from PyQt5.QtCore import QLocale
from ucoinpy.documents.peer import BMAEndpoint

from sakia.core import Account, Community, Wallet
from sakia.core.app import Application
from sakia.core.net import Network, Node
from sakia.core.net.api.bma.access import BmaAccess
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.graphs.wot_tab import WotTabWidget
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain


class TestWotTab(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50003)
        self.node = Node("test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.14.0", 0)
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

        self.wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        # Salt/password : "testsakia/testsakia"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testsakia", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [self.community], [self.wallet], [], self.identities_registry)

        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testsakia"
        self.password_asker.remember = True

    def tearDown(self):
        self.tearDownQuamash()

    def test_empty_wot_tab(self):
        mock = nice_blockchain.get_mock(self.lp)
        time.sleep(2)
        wot_tab = WotTabWidget(self.application)
        future = asyncio.Future()

        def open_widget():
            wot_tab.widget.show()
            return future

        async def async_open_widget():
            srv, port, url = await mock.create_server()
            self.addCleanup(srv.close)
            self.endpoint.port = port
            await open_widget()

        def close_dialog():
            if wot_tab.widget.isVisible():
                wot_tab.widget.close()
            future.set_result(True)

        async def exec_test():
            await asyncio.sleep(1)
            self.assertTrue(wot_tab.widget.isVisible())
            self.lp.call_soon(close_dialog)

        asyncio.ensure_future(exec_test())
        self.lp.call_later(15, close_dialog)
        self.lp.run_until_complete(async_open_widget())

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()
