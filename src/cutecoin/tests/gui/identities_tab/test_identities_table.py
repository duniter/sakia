import sys
import unittest
import asyncio
import quamash
import logging
import time
from ucoinpy.documents.peer import BMAEndpoint as PyBMAEndpoint
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QLocale, Qt, QPoint
from PyQt5.QtTest import QTest
from cutecoin.core.net.api import bma as qtbma
from cutecoin.tests.mocks.bma import nice_blockchain
from cutecoin.tests.mocks.access_manager import MockNetworkAccessManager
from cutecoin.core.registry.identities import IdentitiesRegistry
from cutecoin.gui.identities_tab import IdentitiesTabWidget
from cutecoin.gui.password_asker import PasswordAskerDialog
from cutecoin.core.app import Application
from cutecoin.core import Account, Community, Wallet
from cutecoin.core.net import Network, Node
from cutecoin.core.net.endpoint import BMAEndpoint
from cutecoin.core.net.api.bma.access import BmaAccess
from cutecoin.tests import get_application


class TestIdentitiesTable(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        self.network_manager = MockNetworkAccessManager()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.network_manager, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint(PyBMAEndpoint("", "127.0.0.1", "", 50000))
        self.node = Node(self.network_manager, "test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         qtbma.blockchain.Block.null_value, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.14.0", 0)
        self.network = Network.create(self.network_manager, self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

        self.wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        # Salt/password : "testcutecoin/testcutecoin"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testcutecoin", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [self.community], [self.wallet], [], self.identities_registry)

        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testcutecoin"
        self.password_asker.remember = True

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_search_identity_found(self):
        mock = nice_blockchain.get_mock()
        time.sleep(2)
        logging.debug(mock.pretend_url)
        self.network_manager.set_mock_path(mock.pretend_url)
        identities_tab = IdentitiesTabWidget(self.application)
        identities_tab.change_account(self.account, self.password_asker)
        identities_tab.change_community(self.community)
        future = asyncio.Future()

        def open_widget():
            identities_tab.show()
            return future

        def close_dialog():
            if identities_tab.isVisible():
                identities_tab.close()
            future.set_result(True)

        @asyncio.coroutine
        def exec_test():
            yield from asyncio.sleep(2)
            urls = [mock.get_request(i).url for i in range(0, 3)]
            self.assertTrue('/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ' in urls,
                            msg="Not found in {0}".format(urls))
            self.assertTrue('/wot/certified-by/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ' in urls,
                            msg="Not found in {0}".format(urls))

            # requests 1 to 3 are for getting certifiers-of and certified-by
            # on john, + a lookup

            QTest.keyClicks(identities_tab.edit_textsearch, "doe")
            QTest.mouseClick(identities_tab.button_search, Qt.LeftButton)
            yield from asyncio.sleep(2)
            self.assertEqual(mock.get_request(3).method, 'GET')
            self.assertEqual(mock.get_request(3).url,
                             '/blockchain/parameters')
            self.assertEqual(mock.get_request(4).method, 'GET')
            self.assertEqual(mock.get_request(4).url,
                             '/wot/lookup/doe')
            self.assertEqual(mock.get_request(5).method, 'GET')
            self.assertEqual(mock.get_request(5).url,
                             '/wot/certifiers-of/FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn')
            self.assertEqual(identities_tab.table_identities.model().rowCount(), 1)
            yield from asyncio.sleep(2)
            self.lp.call_soon(close_dialog)

        asyncio.async(exec_test())
        self.lp.call_later(15, close_dialog)
        self.lp.run_until_complete(open_widget())
        mock.delete_mock()

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()
