import sys
import unittest
import asyncio
import logging
from duniterpy.key import ScryptParams
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.process_cfg_account import ProcessConfigureAccount
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.core.app import Application
from sakia.core.account import Account
from sakia.tests import QuamashTest


class ProcessAddCommunity(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry({})

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False
        # Salt/password : "testsakia/testsakia"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testsakia", "B7J4sopyfqzi3uh4Gzsdnp1XHc87NaxY7rqW2exgivCa",
                               ScryptParams(4096, 16, 1),
                               "test", [], [], [], self.identities_registry)
        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testsakia"
        self.password_asker.remember = True

    def tearDown(self):
        self.tearDownQuamash()

    def test_create_account(self):
        process_account = ProcessConfigureAccount(self.application,
                                                    None)

        def close_dialog():
            if process_account.isVisible():
                process_account.close()

        async def exec_test():
            QTest.keyClicks(process_account.edit_account_name, "test")
            self.assertEqual(process_account.stacked_pages.currentWidget(),
                             process_account.page_init,
                             msg="Current widget : {0}".format(process_account.stacked_pages.currentWidget().objectName()))
            QTest.mouseClick(process_account.button_next, Qt.LeftButton)
            await asyncio.sleep(1)

            self.assertEqual(process_account.stacked_pages.currentWidget(),
                             process_account.page_gpg,
                             msg="Current widget : {0}".format(process_account.stacked_pages.currentWidget().objectName()))
            QTest.keyClicks(process_account.edit_salt, "testsakia")
            self.assertFalse(process_account.button_next.isEnabled())
            self.assertFalse(process_account.button_generate.isEnabled())
            QTest.keyClicks(process_account.edit_password, "testsakia")
            self.assertFalse(process_account.button_next.isEnabled())
            self.assertFalse(process_account.button_generate.isEnabled())
            QTest.keyClicks(process_account.edit_password_repeat, "wrongpassword")
            self.assertFalse(process_account.button_next.isEnabled())
            self.assertFalse(process_account.button_generate.isEnabled())
            process_account.edit_password_repeat.setText("")
            QTest.keyClicks(process_account.edit_password_repeat, "testsakia")
            self.assertTrue(process_account.button_next.isEnabled())
            self.assertTrue(process_account.button_generate.isEnabled())
            QTest.mouseClick(process_account.button_generate, Qt.LeftButton)
            self.assertEqual(process_account.label_info.text(),
                             "B7J4sopyfqzi3uh4Gzsdnp1XHc87NaxY7rqW2exgivCa")
            QTest.mouseClick(process_account.button_next, Qt.LeftButton)
            await asyncio.sleep(1)

            self.assertEqual(process_account.stacked_pages.currentWidget(),
                             process_account.page__communities,
                             msg="Current widget : {0}".format(process_account.stacked_pages.currentWidget().objectName()))
            process_account.password_asker.password = "testsakia"
            process_account.password_asker.remember = True
            await asyncio.sleep(1)
            QTest.mouseClick(process_account.button_next, Qt.LeftButton)
            self.assertEqual(len(self.application.accounts), 1)
            await asyncio.sleep(0.1)
            self.assertEqual(self.application.current_account.name, "test")
            self.assertEqual(self.application.preferences['account'], "test")
            self.assertEqual(len(self.application.current_account.wallets), 1)
            await asyncio.sleep(1)

        self.lp.call_later(10, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(process_account.async_exec())

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger().setLevel( logging.DEBUG )
    unittest.main()
