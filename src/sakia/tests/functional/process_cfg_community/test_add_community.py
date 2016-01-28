import sys
import unittest
import asyncio
import quamash
import logging
import time
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from sakia.tests.mocks.bma import new_blockchain, nice_blockchain
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.process_cfg_community import ProcessConfigureCommunity
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
        self.account = Account("testsakia", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [], [], [], self.identities_registry)
        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testsakia"
        self.password_asker.remember = True

    def tearDown(self):
        self.tearDownQuamash()

    def test_register_community_empty_blockchain(self):
        mock = new_blockchain.get_mock(self.lp)
        time.sleep(2)
        process_community = ProcessConfigureCommunity(self.application,
                                                    self.account,
                                                    None, self.password_asker)

        def close_dialog():
            if process_community.isVisible():
                process_community.close()

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.addCleanup(srv.close)
            await asyncio.sleep(1)
            QTest.mouseClick(process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(process_community.spinbox_port, Qt.LeftButton)
            process_community.spinbox_port.setValue(port)
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(process_community.spinbox_port.value(), port)
            QTest.mouseClick(process_community.button_register, Qt.LeftButton)
            await asyncio.sleep(1)
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')
            self.assertEqual(process_community._step_init.node.endpoint.port, port)
            self.assertEqual(mock.get_request(1).method, 'GET')
            self.assertEqual(mock.get_request(1).url,
                             '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            for i in range(2, 5):
                self.assertEqual(mock.get_request(i).method, 'GET')
                self.assertEqual(mock.get_request(i).url,
                                 '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            await asyncio.sleep(5)
            self.assertEqual(mock.get_request(5).method, 'GET')
            self.assertEqual(mock.get_request(5).url,
                             '/wot/lookup/john')
            for i in range(6, 8):
                self.assertEqual(mock.get_request(i).method, 'GET')
                self.assertEqual(mock.get_request(i).url,
                                 '/wot/lookup/john')

            self.assertEqual(mock.get_request(8).url[:8], '/wot/add')
            self.assertEqual(mock.get_request(8).method, 'POST')
            self.assertEqual(process_community.label_error.text(), "Broadcasting identity...")
            await asyncio.sleep(1)

            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_add_nodes,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            QTest.mouseClick(process_community.button_next, Qt.LeftButton)

        self.lp.call_later(15, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(process_community.async_exec())
        self.assertEqual(process_community.result(), QDialog.Accepted)

    def test_connect_community_empty_blockchain(self):
        mock = new_blockchain.get_mock(self.lp)
        time.sleep(2)
        process_community = ProcessConfigureCommunity(self.application,
                                                    self.account,
                                                    None, self.password_asker)

        def close_dialog():
            if process_community.isVisible():
                process_community.close()

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.addCleanup(srv.close)

            await asyncio.sleep(1)
            QTest.mouseClick(process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(process_community.spinbox_port, Qt.LeftButton)
            process_community.spinbox_port.setValue(port)
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(process_community.spinbox_port.value(), port)
            QTest.mouseClick(process_community.button_connect, Qt.LeftButton)
            await asyncio.sleep(2)
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')
            self.assertEqual(mock.get_request(1).method, 'GET')
            self.assertEqual(mock.get_request(1).url,
                             '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            for i in range(2, 5):
                self.assertEqual(mock.get_request(i).method, 'GET')
                self.assertEqual(mock.get_request(i).url,
                                 '/wot/lookup/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.label_error.text(), "Could not find your identity on the network.")
            process_community.close()

        self.lp.call_later(15, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(process_community.async_exec())

    def test_connect_community_wrong_pubkey(self):
        mock = nice_blockchain.get_mock(self.lp)
        time.sleep(2)
        self.account.pubkey = "wrong_pubkey"
        process_community = ProcessConfigureCommunity(self.application,
                                                    self.account,
                                                    None, self.password_asker)

        def close_dialog():
            if process_community.isVisible():
                process_community.close()

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.addCleanup(srv.close)
            await asyncio.sleep(1)
            QTest.mouseClick(process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(process_community.spinbox_port, Qt.LeftButton)
            process_community.spinbox_port.setValue(port)
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(process_community.spinbox_port.value(), port)
            QTest.mouseClick(process_community.button_connect, Qt.LeftButton)
            await asyncio.sleep(1)
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')
            self.assertEqual(mock.get_request(1).method, 'GET')
            self.assertEqual(mock.get_request(1).url,
                             '/wot/lookup/john')
            self.assertEqual(process_community.label_error.text(), """Your pubkey or UID is different on the network.
Yours : wrong_pubkey, the network : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ""")
            process_community.close()

        self.lp.call_later(15, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(process_community.async_exec())
        self.assertEqual(process_community.result(), QDialog.Rejected)

    def test_connect_community_wrong_uid(self):
        mock = nice_blockchain.get_mock(self.lp)
        time.sleep(2)
        self.account.name = "wrong_uid"
        process_community = ProcessConfigureCommunity(self.application,
                                                    self.account,
                                                    None, self.password_asker)

        def close_dialog():
            if process_community.isVisible():
                process_community.close()

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.addCleanup(srv.close)
            await asyncio.sleep(1)
            QTest.mouseClick(process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(process_community.spinbox_port, Qt.LeftButton)
            process_community.spinbox_port.setValue(port)
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(process_community.spinbox_port.value(), port)
            QTest.mouseClick(process_community.button_connect, Qt.LeftButton)
            await asyncio.sleep(1)
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')
            self.assertEqual(mock.get_request(1).method, 'GET')
            self.assertEqual(mock.get_request(1).url,
                             '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            self.assertEqual(process_community.label_error.text(), """Your pubkey or UID is different on the network.
Yours : wrong_uid, the network : john""")
            process_community.close()

        self.lp.call_later(15, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(process_community.async_exec())
        self.assertEqual(process_community.result(), QDialog.Rejected)

    def test_connect_community_success(self):
        mock = nice_blockchain.get_mock(self.lp)
        time.sleep(2)
        process_community = ProcessConfigureCommunity(self.application,
                                                    self.account,
                                                    None, self.password_asker)

        def close_dialog():
            if process_community.isVisible():
                process_community.close()

        async def exec_test():
            srv, port, url = await mock.create_server()
            self.addCleanup(srv.close)
            await asyncio.sleep(1)
            QTest.mouseClick(process_community.lineedit_server, Qt.LeftButton)
            QTest.keyClicks(process_community.lineedit_server, "127.0.0.1")
            QTest.mouseDClick(process_community.spinbox_port, Qt.LeftButton)
            process_community.spinbox_port.setValue(port)
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_node,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            self.assertEqual(process_community.lineedit_server.text(), "127.0.0.1")
            self.assertEqual(process_community.spinbox_port.value(), port)
            QTest.mouseClick(process_community.button_connect, Qt.LeftButton)
            await asyncio.sleep(1)
            self.assertEqual(mock.get_request(0).method, 'GET')
            self.assertEqual(mock.get_request(0).url, '/network/peering')
            self.assertEqual(mock.get_request(1).method, 'GET')
            self.assertEqual(mock.get_request(1).url,
                             '/wot/certifiers-of/7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ')
            self.assertEqual(process_community.stacked_pages.currentWidget(),
                             process_community.page_add_nodes,
                             msg="Current widget : {0}".format(process_community.stacked_pages.currentWidget().objectName()))
            QTest.mouseClick(process_community.button_next, Qt.LeftButton)

        self.lp.call_later(15, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(process_community.async_exec())