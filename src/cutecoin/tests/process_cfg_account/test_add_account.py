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
from cutecoin.gui.process_cfg_account import ProcessConfigureAccount
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
        self.identities_registry = IdentitiesRegistry({})

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

    def test_create_account(self):
        process_account = ProcessConfigureAccount(self.application,
                                                    None)

        @asyncio.coroutine
        def open_dialog(process_account):
            result = yield from process_account.async_exec()
            self.assertEqual(result, QDialog.Accepted)

        def close_dialog():
            if process_account.isVisible():
                process_account.close()

        @asyncio.coroutine
        def exec_test():
            QTest.keyClicks(process_account.edit_account_name, "test")
            self.assertEqual(process_account.stacked_pages.currentWidget(),
                             process_account.page_init,
                             msg="Current widget : {0}".format(process_account.stacked_pages.currentWidget().objectName()))
            QTest.mouseClick(process_account.button_next, Qt.LeftButton)

            self.assertEqual(process_account.stacked_pages.currentWidget(),
                             process_account.page_gpg,
                             msg="Current widget : {0}".format(process_account.stacked_pages.currentWidget().objectName()))

            QTest.keyClicks(process_account.edit_salt, "testcutecoin")
            self.assertFalse(process_account.button_next.isEnabled())
            self.assertFalse(process_account.button_generate.isEnabled())
            QTest.keyClicks(process_account.edit_password, "testcutecoin")
            self.assertFalse(process_account.button_next.isEnabled())
            self.assertFalse(process_account.button_generate.isEnabled())
            QTest.keyClicks(process_account.edit_password_repeat, "wrongpassword")
            self.assertFalse(process_account.button_next.isEnabled())
            self.assertFalse(process_account.button_generate.isEnabled())
            process_account.edit_password_repeat.setText("")
            QTest.keyClicks(process_account.edit_password_repeat, "testcutecoin")
            self.assertTrue(process_account.button_next.isEnabled())
            self.assertTrue(process_account.button_generate.isEnabled())
            QTest.mouseClick(process_account.button_generate, Qt.LeftButton)
            self.assertEqual(process_account.label_info.text(),
                             "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ")
            QTest.mouseClick(process_account.button_next, Qt.LeftButton)

            self.assertEqual(process_account.stacked_pages.currentWidget(),
                             process_account.page__communities,
                             msg="Current widget : {0}".format(process_account.stacked_pages.currentWidget().objectName()))
            process_account.password_asker.password = "testcutecoin"
            process_account.password_asker.remember = True
            yield from asyncio.sleep(1)
            QTest.mouseClick(process_account.button_next, Qt.LeftButton)
            self.assertEqual(len(self.application.accounts), 1)
            self.assertEqual(self.application.current_account.name, "test")
            self.assertEqual(self.application.preferences['account'], "test")

        self.lp.call_later(10, close_dialog)
        asyncio.async(exec_test())
        self.lp.run_until_complete(open_dialog(process_account))

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()
