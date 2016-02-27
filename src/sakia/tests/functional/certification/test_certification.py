import sys
import unittest
import asyncio
import time
import logging
import aiohttp
from ucoinpy.documents.peer import BMAEndpoint
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox, QApplication
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from sakia.tests.mocks.bma import init_new_community
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.certification import CertificationDialog, Ui_CertificationDialog
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.core.app import Application
from sakia.core import Account, Community, Wallet
from sakia.core.net import Network, Node
from sakia.core.net.api.bma.access import BmaAccess
from sakia.tests import QuamashTest


class TestCertificationDialog(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry({})

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.mock_new_community = init_new_community.get_mock(self.lp)

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50010)
        self.node = Node(self.mock_new_community.peer(),
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.14.0", 0, session=aiohttp.ClientSession())
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

        self.wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        # Salt/password : "testsakia/testsakia"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testsakia", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [self.community], [self.wallet], [], self.identities_registry)
        self.account.notifications['warning_certifying_first_time'] = False
        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testsakia"
        self.password_asker.remember = True

    def tearDown(self):
        self.tearDownQuamash()

    def test_certification_init_community(self):
        time.sleep(2)
        certification_dialog = CertificationDialog(self.application,
                                                   self.account,
                                                   self.password_asker,
                                                   QDialog(),
                                                    Ui_CertificationDialog())

        async def open_dialog(certification_dialog):
            srv, port, url = await self.mock_new_community.create_server()
            self.addCleanup(srv.close)
            await certification_dialog.async_exec()

        def close_dialog():
            if certification_dialog.widget.isVisible():
                certification_dialog.widget.close()

        async def exec_test():
            await asyncio.sleep(1)
            QTest.mouseClick(certification_dialog.ui.radio_pubkey, Qt.LeftButton)
            QTest.keyClicks(certification_dialog.ui.edit_pubkey, "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
            QTest.mouseClick(certification_dialog.ui.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
            await asyncio.sleep(3)
            topWidgets = QApplication.topLevelWidgets()
            for w in topWidgets:
                if type(w) is QMessageBox:
                    QTest.keyClick(w, Qt.Key_Enter)

        self.lp.call_later(10, close_dialog)
        asyncio.ensure_future(exec_test())
        self.lp.run_until_complete(open_dialog(certification_dialog))
