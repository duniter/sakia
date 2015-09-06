import sys
import unittest
import asyncio
import quamash
import logging
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from cutecoin.tests.mocks.bma import new_blockchain
from cutecoin.tests.mocks.access_manager import MockNetworkAccessManager
from cutecoin.core.registry.identities import IdentitiesRegistry
from cutecoin.gui.process_cfg_community import ProcessConfigureCommunity
from cutecoin.gui.password_asker import PasswordAskerDialog
from cutecoin.core.app import Application
from cutecoin.core.account import Account
from cutecoin.tests import get_application


class ProcessAddCommunity(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        self.network_manager = MockNetworkAccessManager()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)
        self.identities_registry = IdentitiesRegistry()

        self.application = Application(self.qapplication, self.lp, self.network_manager, self.identities_registry)
        self.application.preferences['notifications'] = False
        # Salt/password : "testcutecoin/testcutecoin"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testcutecoin", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "test", [], [], [], self.identities_registry)
        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testcutecoin"
        self.password_asker.remember = True

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_add_community_empty_blockchain(self):
        process_community = ProcessConfigureCommunity(self.application,
                                                    self.account,
                                                    None, self.password_asker)

        @asyncio.coroutine
        def open_dialog(process_community):
            result = yield from process_community.async_exec()
            self.assertEqual(result, QDialog.Accepted)

        def close_dialog():
            if process_community.isVisible():
                process_community.close()

        @asyncio.coroutine
        def exec_test():
            mock = new_blockchain.get_mock()
            logging.debug(mock.pretend_url)
            yield from asyncio.sleep(1)
            self.network_manager.set_mock_path(mock.pretend_url)
            QTest.mouseClick(process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(process_community.spinbox_port, Qt.LeftButton)
            process_community.spinbox_port.setValue(50000)
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(process_community.spinbox_port.value(), 50000)
            QTest.mouseClick(process_community.button_register, Qt.LeftButton)
            yield from asyncio.sleep(1)
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')
            self.assertEqual(mock.get_request(1).method, 'GET')
            self.assertEqual(mock.get_request(1).url,
                             '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            for i in range(2, 5):
                self.assertEqual(mock.get_request(i).method, 'GET')
                self.assertEqual(mock.get_request(i).url,
                                 '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')

            self.assertEqual(mock.get_request(6).method, 'POST')
            self.assertEqual(mock.get_request(6).url[:8], '/wot/add')
            self.assertEqual(process_community.label_error.text(), "Broadcasting identity...")
            yield from asyncio.sleep(1)

            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_add_nodes,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            QTest.mouseClick(process_community.button_next, Qt.LeftButton)

        self.lp.call_later(15, close_dialog)
        asyncio.async(exec_test())
        self.lp.run_until_complete(open_dialog(process_community))

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()
