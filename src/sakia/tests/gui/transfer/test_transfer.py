import sys
import unittest
import asyncio
import quamash
import time
import logging
from quamash import QApplication
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QMessageBox
from PyQt5.QtCore import QLocale, Qt
from PyQt5.QtTest import QTest
from ucoinpy.api.bma import API
from sakia.tests.mocks.monkeypatch import pretender_reversed
from sakia.tests.mocks.bma import nice_blockchain
from sakia.core.registry.identities import IdentitiesRegistry
from sakia.gui.transfer import TransferMoneyDialog
from sakia.gui.password_asker import PasswordAskerDialog
from sakia.core.app import Application
from sakia.core import Account, Community, Wallet
from sakia.core.net import Network, Node
from ucoinpy.documents.peer import BMAEndpoint
from sakia.core.net.api.bma.access import BmaAccess
from sakia.tests import QuamashTest
from ucoinpy.api import bma


class TestTransferDialog(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))
        self.identities_registry = IdentitiesRegistry({})

        self.application = Application(self.qapplication, self.lp, self.identities_registry)
        self.application.preferences['notifications'] = False

        self.endpoint = BMAEndpoint("", "127.0.0.1", "", 50000)
        self.node = Node("test_currency", [self.endpoint],
                         "", "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk",
                         None, Node.ONLINE,
                         time.time(), {}, "ucoin", "0.14.0", 0)
        self.network = Network.create(self.node)
        self.bma_access = BmaAccess.create(self.network)
        self.community = Community("test_currency", self.network, self.bma_access)

        self.wallet = Wallet(0, "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                             "Wallet 1", self.identities_registry)

        # Salt/password : "testsakia/testsakia"
        # Pubkey : 7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ
        self.account = Account("testsakia", "7Aqw6Efa9EzE7gtsc8SveLLrM7gm6NEGoywSv4FJx6pZ",
                               "john", [self.community], [self.wallet], [], self.identities_registry)

        self.password_asker = PasswordAskerDialog(self.account)
        self.password_asker.password = "testsakia"
        self.password_asker.remember = True

    def tearDown(self):
        self.tearDownQuamash()

    def test_transfer_nice_community(self):
        mock = nice_blockchain.get_mock()
        time.sleep(2)
        logging.debug(mock.pretend_url)
        API.reverse_url = pretender_reversed(mock.pretend_url)
        transfer_dialog = TransferMoneyDialog(self.application,
                                              self.account,
                                              self.password_asker,
                                              self.community,
                                              None)
        self.account.wallets[0].init_cache(self.application, self.community)

        @asyncio.coroutine
        def open_dialog(certification_dialog):
            result = yield from certification_dialog.async_exec()
            self.assertEqual(result, QDialog.Accepted)

        def close_dialog():
            if transfer_dialog.isVisible():
                transfer_dialog.close()

        @asyncio.coroutine
        def exec_test():
            yield from asyncio.sleep(1)
            self.account.wallets[0].caches[self.community.currency].available_sources = yield from self.wallet.sources(self.community)
            QTest.mouseClick(transfer_dialog.radio_pubkey, Qt.LeftButton)
            QTest.keyClicks(transfer_dialog.edit_pubkey, "FADxcH5LmXGmGFgdixSes6nWnC4Vb4pRUBYT81zQRhjn")
            transfer_dialog.spinbox_amount.setValue(10)
            QTest.mouseClick(transfer_dialog.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
            yield from asyncio.sleep(1)
            topWidgets = QApplication.topLevelWidgets()
            for w in topWidgets:
                if type(w) is QMessageBox:
                    QTest.keyClick(w, Qt.Key_Enter)

        self.lp.call_later(15, close_dialog)
        asyncio.async(exec_test())
        self.lp.run_until_complete(open_dialog(transfer_dialog))
        mock.delete_mock()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr)
    logging.getLogger().setLevel(logging.DEBUG)
    unittest.main()
