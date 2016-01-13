import unittest
from PyQt5.QtWidgets import QDialog, QFileDialog
from PyQt5.QtCore import QLocale, QTimer
from sakia.gui.mainwindow import MainWindow
from sakia.core.app import Application
from sakia.tests import QuamashTest
from sakia.core.registry.identities import IdentitiesRegistry

# Qapplication cause a core dumped when re-run in setup
# set it as global var

class MainWindowDialogsTest(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        self.application = Application(self.qapplication, self.lp, IdentitiesRegistry())
        self.main_window = MainWindow(self.application)

    def tearDown(self):
        self.tearDownQuamash()

    def test_action_about(self):
        #select menu
        self.main_window.actionAbout.trigger()
        widgets = self.qapplication.topLevelWidgets()
        for widget in widgets:
            if isinstance(widget, QDialog):
                if widget.isVisible():
                    self.assertEqual('AboutPopup', widget.objectName())
                    widget.close()
                    break

    def test_action_add_account(self):
        #asynchronous test, cause dialog is waiting user response
        QTimer.singleShot(1, self._async_test_action_add_account)
        #select menu
        self.main_window.action_add_account.trigger()

    def _async_test_action_add_account(self):
        widgets = self.qapplication.topLevelWidgets()
        for widget in widgets:
            if isinstance(widget, QDialog):
                if widget.isVisible():
                    try:
                        self.assertEqual('AccountConfigurationDialog', widget.objectName())
                        break
                    finally:
                        widget.close()

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
        self.main_window.action_export.trigger()

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
