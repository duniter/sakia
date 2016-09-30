import asyncio
import time
import unittest

import aiohttp
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from sakia.core.net import Network, Node
from sakia.core.net.api.bma.access import BmaAccess
from sakia.gui.identities_tab import IdentitiesTabWidget

from sakia.app import Application
from sakia.core import Account, Community, Wallet
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.tests import QuamashTest
from sakia.tests.mocks.bma import nice_blockchain


class TestIdentitiesTable(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.mock_nice_blockchain = nice_blockchain.get_mock(self.lp)
        self.node = Node(self.mock_nice_blockchain.peer(),
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "duniter", "0.14.0", 0, session=aiohttp.ClientSession())
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

    def test_search_identity_found(self):
        time.sleep(2)
        identities_tab = IdentitiesTabWidget(self.application)
        future = asyncio.Future()

        def open_widget():
            identities_tab.widget.show()
            return future

        def close_dialog():
            if identities_tab.widget.isVisible():
                identities_tab.widget.close()
            future.set_result(True)

        async def exec_test():
            srv, port, url = await self.mock_nice_blockchain.create_server()
            self.addCleanup(srv.close)

            identities_tab.change_account(self.account, self.password_asker)
            identities_tab.change_community(self.community)
            await asyncio.sleep(1)

            QTest.keyClicks(identities_tab.ui.edit_textsearch, "doe")
            QTest.mouseClick(identities_tab.ui.button_search, Qt.LeftButton)
            await asyncio.sleep(2)

            self.assertEqual(identities_tab.ui.table_identities.model().rowCount(), 1)
            await self.mock_nice_blockchain.close()
            self.lp.call_soon(close_dialog)

        asyncio.ensure_future(exec_test())
        self.lp.call_later(15, close_dialog)
        self.lp.run_until_complete(open_widget())
