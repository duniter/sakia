import sys
import unittest
import asyncio
import quamash
import time
import logging
from ucoinpy.documents.peer import BMAEndpoint
from quamash import QApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from ucoinpy.api.bma import API
from cutecoin.tests.mocks.monkeypatch import pretender_reversed
from cutecoin.tests.mocks.bma import init_new_community
from cutecoin.core.registry.identities import IdentitiesRegistry
from cutecoin.gui.preferences import PreferencesDialog
from cutecoin.core.app import Application
from cutecoin.core import Account, Community, Wallet
from cutecoin.core.net import Network, Node
from cutecoin.core.net.api.bma.access import BmaAccess
from cutecoin.tests import get_application, unitttest_exception_handler
from ucoinpy.api import bma


class TestCertificationDialog(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)
        #self.lp.set_exception_handler(lambda lp, ctx : unitttest_exception_handler(self, lp, ctx))
        self.identities_registry = IdentitiesRegistry({})

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_preferences_default(self):
        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        preferences_dialog = PreferencesDialog(self.application)
        self.assertEqual(preferences_dialog.combo_account.currentText(),
                         self.application.preferences['account'])
        self.assertEqual(preferences_dialog.combo_language.currentText(),
                         self.application.preferences['lang'])
        self.assertEqual(preferences_dialog.combo_referential.currentIndex(),
                         self.application.preferences['ref'])
        self.assertEqual(preferences_dialog.checkbox_expertmode.isChecked(),
                         self.application.preferences['expert_mode'])
        self.assertEqual(preferences_dialog.checkbox_maximize.isChecked(),
                         self.application.preferences['maximized'])
        self.assertEqual(preferences_dialog.checkbox_notifications.isChecked(),
                         self.application.preferences['notifications'])
        self.assertEqual(preferences_dialog.checkbox_proxy.isChecked(),
                         self.application.preferences['enable_proxy'])
        self.assertEqual(preferences_dialog.edit_proxy_address.text(),
                         self.application.preferences['proxy_address'])
        self.assertEqual(preferences_dialog.spinbox_proxy_port.value(),
                         self.application.preferences['proxy_port'])
        self.assertEqual(preferences_dialog.checkbox_international_system.isChecked(),
                         self.application.preferences['international_system_of_units'])
        self.assertEqual(preferences_dialog.checkbox_auto_refresh.isChecked(),
                         self.application.preferences['auto_refresh'])

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
