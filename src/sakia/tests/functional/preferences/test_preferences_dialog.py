import sys
import unittest
import asyncio
import quamash
import logging
from PyQt5.QtCore import QLocale
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.preferences import PreferencesDialog
from sakia.core.app import Application
from sakia.tests import QuamashTest
from duniterpy.api import bma


class TestPreferencesDialog(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry({})

    def tearDown(self):
        self.tearDownQuamash()

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
