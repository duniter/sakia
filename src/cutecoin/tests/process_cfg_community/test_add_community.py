import sys
import unittest
import os
import asyncio
import quamash
import logging
import time
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from cutecoin.tests.mocks.bma import new_blockchain
from cutecoin.tests.mocks.access_manager import MockNetworkAccessManager
from cutecoin.tests.stubs.core.registry.identities import IdentitiesRegistry
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

        self.application = Application(self.qapplication, self.lp, self.network_manager, None)
        self.identities_registry = IdentitiesRegistry()
        self.account = Account("test", "test", "test", [], [], [], self.identities_registry)
        self.password_asker = PasswordAskerDialog(self.account)

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_add_community_empty_blockchain(self):
        self.process_community = ProcessConfigureCommunity(self.application, self.account, None, self.password_asker)

        @asyncio.coroutine
        def exec_test():
            mock = new_blockchain.get_mock()
            logging.debug(mock.pretend_url)
            self.network_manager.set_mock_path(mock.pretend_url)
            QTest.mouseClick(self.process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(self.process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(self.process_community.spinbox_port, Qt.LeftButton)
            self.process_community.spinbox_port.setValue(50000)
            self.assertEqual(self.process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(self.process_community.spinbox_port.value(), 50000)
            QTest.mouseClick(self.process_community.button_checknode, Qt.LeftButton)
            yield from asyncio.sleep(3)
            self.assertEqual(self.process_community.button_checknode.text(), "Ok !")
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')

        self.lp.run_until_complete(asyncio.wait_for(exec_test(), timeout=10))

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()
