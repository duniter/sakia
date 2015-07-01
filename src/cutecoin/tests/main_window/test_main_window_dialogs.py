import sys
import unittest
import gc
import os
import asyncio
import quamash
import PyQt5
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QLocale, QTimer
from PyQt5.QtNetwork import QNetworkAccessManager
from cutecoin.gui.mainwindow import MainWindow
from cutecoin.core.app import Application

from cutecoin.tests.stubs.core.registry import IdentitiesRegistry

# Qapplication cause a core dumped when re-run in setup
# set it as global var

class MainWindowDialogsTest(unittest.TestCase):
    def setUp(self):
        QLocale.setDefault(QLocale("en_GB"))
        self.qapplication = quamash.QApplication([])
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)

        self.additional_exceptions = []

        self.orig_excepthook = sys.excepthook

        def except_handler(loop, ctx):
            self.additional_exceptions.append(ctx)

        def excepthook(type, *args):
            self.lp.stop()
            self.orig_excepthook(type, *args)

        sys.excepthook = excepthook

        self.lp.set_exception_handler(except_handler)

        network_manager = QNetworkAccessManager()

        self.application = Application(self.qapplication, self.lp, network_manager, IdentitiesRegistry())
        self.main_window = MainWindow(self.application)

    def tearDown(self):
        # delete all top widgets from main QApplication
        sys.excepthook = self.orig_excepthook
        self.qapplication.quit()
        self.lp.stop()
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)
            self.qapplication.exit()

        for exc in self.additional_exceptions:
            if (
                os.name == 'nt' and
                isinstance(exc['exception'], WindowsError) and
                exc['exception'].winerror == 6
            ):
                # ignore Invalid Handle Errors
                continue
            raise exc['exception']

    # def test_action_about(self):
    #     #select menu
    #     self.main_window.actionAbout.trigger()
    #     widgets = self.qapplication.topLevelWidgets()
    #     for widget in widgets:
    #         if isinstance(widget, PyQt5.QtWidgets.QDialog):
    #             if widget.isVisible():
    #                 self.assertEqual('AboutPopup', widget.objectName())
    #                 widget.close()
    #                 break
    #
    # def test_action_add_account(self):
    #     pass
        # asynchronous test, cause dialog is waiting user response
        #QTimer.singleShot(1, self._async_test_action_add_account)
        # select menu
        #self.main_window.action_add_account.trigger()
    #
    # def _async_test_action_add_account(self):
    #     widgets = self.qapplication.topLevelWidgets()
    #     for widget in widgets:
    #         if isinstance(widget, PyQt5.QtWidgets.QDialog):
    #             if widget.isVisible():
    #                 self.assertEqual('AccountConfigurationDialog', widget.objectName())
    #                 widget.close()
    #                 break

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
    # def test_action_export_account(self):
    #     pass
        # select menu
        # self.main_window.action_export.trigger()
        #
        # widgets = self.qapplication.topLevelWidgets()
        # for widget in widgets:
        #     if isinstance(widget, PyQt5.QtWidgets.QFileDialog):
        #         if widget.isVisible():
        #             self.assertEqual('ExportFileDialog', widget.objectName())
        #             widget.close()
        #             break
    def test_empty(self):
        self.assertEquals(1, 1)

if __name__ == '__main__':
    unittest.main()
