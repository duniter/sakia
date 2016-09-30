import asyncio
import unittest

from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QDialog, QFileDialog
from sakia.gui.mainwindow import MainWindow

from sakia.app import Application
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.tests import QuamashTest


class MainWindowDialogsTest(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        self.application = Application(self.qapplication, self.lp, IdentitiesRegistry())
        self.main_window = MainWindow.startup(self.application)

    def tearDown(self):
        self.main_window.widget.close()
        self.tearDownQuamash()

    def test_action_about(self):
        #select menu
        self.main_window.ui.actionAbout.trigger()
        widgets = self.qapplication.topLevelWidgets()
        for widget in widgets:
            if isinstance(widget, QDialog):
                if widget.isVisible():
                    self.assertEqual('AboutPopup', widget.objectName())
                    widget.close()
                    break

    def test_action_add_account(self):
        async def exec_test():
            self.main_window.ui.action_add_account.trigger()
            await asyncio.sleep(1)
            widgets = self.qapplication.topLevelWidgets()
            for widget in widgets:
                if isinstance(widget, QDialog):
                    if widget.isVisible():
                        try:
                            self.assertEqual('AccountConfigurationDialog', widget.objectName())
                            break
                        finally:
                            widget.close()
        self.lp.run_until_complete(exec_test())

    # fixme: require a app.current_account fixture
    # def test_action_configure_account(self):
    #     # asynchronous test, cause dialog is waiting user response
    #     QTimer.singleShot(0, self._async_test_action_configure_account)
    #     # select about menu
    #     self.main_window.action_configure_parameters.trigger()
    #
    # def _async_test_action_configure_account(self):
    #     widgets = qapplication.topLevelWidgets()
    #     for widget in widgets:
    #         if isinstance(widget, PyQt5.QtWidgets.QDialog):
    #             self.assertEqual(widget.objectName(), 'AccountConfigurationDialog')
    #             self.assertEqual(widget.isVisible(), True)
    #             widget.close()
    #             break
    #
    def test_action_export_account(self):
        #select menu
        self.main_window.ui.action_export.trigger()

        widgets = self.qapplication.topLevelWidgets()
        for widget in widgets:
            if isinstance(widget, QFileDialog):
                if widget.isVisible():
                    try:
                        self.assertEqual('ExportFileDialog', widget.objectName())
                        break
                    finally:
                        widget.close()

if __name__ == '__main__':
    unittest.main()
