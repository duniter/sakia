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
from cutecoin.tests.stubs.core.registry.identities import IdentitiesRegistry
from cutecoin.gui.process_cfg_community import ProcessConfigureCommunity
from cutecoin.gui.password_asker import PasswordAskerDialog
from cutecoin.core.app import Application
from cutecoin.core.account import Account
from cutecoin.tests import get_application


class ProcessAddCommunity(unittest.TestCase):
    test_instance = None
    @staticmethod
    def async_exception_handler(loop, context):
        """
        An exception handler which exists the program if the exception
        was not catch
        :param loop: the asyncio loop
        :param context: the exception context
        """
        message = context.get('message')
        if not message:
            message = 'Unhandled exception in event loop'

        try:
            exception = context['exception']
        except KeyError:
            exc_info = False
        else:
            exc_info = (type(exception), exception, exception.__traceback__)

        log_lines = [message]
        for key in [k for k in sorted(context) if k not in {'message', 'exception'}]:
            log_lines.append('{}: {!r}'.format(key, context[key]))

        unittest.TestCase.fail(ProcessAddCommunity.test_instance, '\n'.join(log_lines))

    def setUp(self):
        ProcessAddCommunity.test_instance = self
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        self.lp.set_exception_handler(ProcessAddCommunity.async_exception_handler)
        asyncio.set_event_loop(self.lp)

        self.application = Application(self.qapplication, self.lp, None, None)
        self.identities_registry = IdentitiesRegistry()
        self.account = Account("test", "test", "test", [], [], [], self.identities_registry)
        self.password_asker = PasswordAskerDialog(self.account)

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_add_community_empty_blockchain(self):
        asyncio.set_event_loop(self.lp)
        self.lp.run_forever()
        mock = new_blockchain.get_mock()
        self.process_community = ProcessConfigureCommunity(self.application,
                                                           self.account, None,
                                                           self.password_asker)
        QTest.mouseClick(self.process_community.lineedit_add_address, Qt.LeftButton)
        QTest.keyClicks(self.process_community.lineedit_add_address, "127.0.0.1")
        QTest.mouseDClick(self.process_community.spinbox_add_port, Qt.LeftButton)
        self.process_community.spinbox_add_port.setValue(50000)
        self.assertEqual(self.process_community.lineedit_add_address.text(), "127.0.0.1")
        self.assertEqual(self.process_community.spinbox_add_port.value(), 50000)
        QTest.mouseClick(self.process_community.button_checknode, Qt.LeftButton)
        self.lp.run_forever()
        QTest.qSleep(10000)
        self.assertEqual(mock.get_request(0).method, 'GET')
        self.assertEqual(mock.get_request(0).url, '/network/peering')
        self.assertEqual(self.process_community.button_checknode.text(), "Ok !")

if __name__ == '__main__':
    unittest.main()
