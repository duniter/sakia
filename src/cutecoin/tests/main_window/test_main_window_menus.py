# -*- coding: utf-8 -*-

import sys
import unittest
import gc
import os
import asyncio
import quamash
from PyQt5.QtWidgets import QApplication, QMenu
from PyQt5.QtCore import QLocale
from cutecoin.gui.mainwindow import MainWindow
from cutecoin.core.app import Application

# Qapplication cause a core dumped when re-run in setup
# set it as global var
qapplication = QApplication(sys.argv)


class MainWindowMenusTest(unittest.TestCase):
    def setUp(self):
        QLocale.setDefault(QLocale("en_GB"))
        self.lp = quamash.QEventLoop(qapplication)
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

        self.application = Application(sys.argv, qapplication, self.lp)
        self.main_window = MainWindow(self.application)

    def tearDown(self):
        # delete all top widgets from main QApplication

        sys.excepthook = self.orig_excepthook

        try:
            self.lp.close()
        finally:
            asyncio.set_event_loop(None)

        for exc in self.additional_exceptions:
            if (
                os.name == 'nt' and
                isinstance(exc['exception'], WindowsError) and
                exc['exception'].winerror == 6
            ):
                # ignore Invalid Handle Errors
                continue
            raise exc['exception']

        lw = qapplication.topLevelWidgets()
        for w in lw:
            del w
        gc.collect()

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

    def test_ignoreme(self):
        return

if __name__ == '__main__':
    unittest.main()
