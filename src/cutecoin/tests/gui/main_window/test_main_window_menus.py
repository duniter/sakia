import sys
import unittest
import os
import asyncio
import quamash
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QLocale
from cutecoin.gui.mainwindow import MainWindow
from cutecoin.core.app import Application
from cutecoin.tests import get_application

class MainWindowMenusTest(unittest.TestCase):
    def setUp(self):
        self.qapplication = get_application()
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(self.qapplication)
        asyncio.set_event_loop(self.lp)

        self.application = Application(self.qapplication, self.lp, None)
        self.main_window = MainWindow(self.application)

    def tearDown(self):
        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

    def test_menubar(self):
        children = self.main_window.menubar.children()
        menus = []
        """:type: list[QMenu]"""
        for child in children:
            if isinstance(child, QMenu):
                menus.append(child)
        self.assertEqual(len(menus), 3)
        self.assertEqual(menus[0].objectName(), 'menu_file')
        self.assertEqual(menus[1].objectName(), 'menu_account')
        self.assertEqual(menus[2].objectName(), 'menu_help')

    def test_menu_account(self):
        actions = self.main_window.menu_account.actions()
        """:type: list[QAction]"""
        self.assertEqual('action_configure_parameters', actions[1].objectName())
        self.assertEqual('action_add_account', actions[2].objectName())
        self.assertEqual('actionCertification', actions[4].objectName())
        self.assertEqual('actionTransfer_money', actions[5].objectName())
        self.assertEqual('action_add_a_contact', actions[7].objectName())
        self.assertEqual(9, len(actions))

    def test_menu_actions(self):
        actions = self.main_window.menu_help.actions()
        """:type: list[QAction]"""
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].objectName(), 'actionAbout')

if __name__ == '__main__':
    unittest.main()
