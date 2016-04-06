import unittest
from unittest.mock import patch, MagicMock, Mock, PropertyMock
from PyQt5.QtCore import QLocale
from sakia.tests import QuamashTest
from sakia.gui.mainwindow import MainWindow


class TestMainWindow(unittest.TestCase, QuamashTest):
    def setUp(self):
        self.setUpQuamash()
        QLocale.setDefault(QLocale("en_GB"))

        self.identity = Mock(spec='sakia.core.registry.Identity')
        self.identity.pubkey = "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        self.identity.uid = "A"

        self.app = MagicMock(autospec='sakia.core.Application')
        self.account_joe = Mock(spec='sakia.core.Account')
        self.account_joe.contacts_changed = Mock()
        self.account_joe.contacts_changed.disconnect = Mock()
        self.account_joe.contacts_changed.connect = Mock()
        self.account_doe = Mock(spec='sakia.core.Account')
        self.account_doe.contacts_changed = Mock()
        self.account_doe.contacts_changed.disconnect = Mock()
        self.account_doe.contacts_changed.connect = Mock()

        def change_current_account(account_name):
            type(self.app).current_account = PropertyMock(return_value=self.account_doe)
        self.app.get_account = Mock(side_effect=lambda name: self.app.accounts[name])
        self.app.change_current_account = Mock(side_effect=change_current_account)
        type(self.app).current_account = PropertyMock(return_value=self.account_joe)
        self.app.accounts = {'joe':self.account_joe,
                             'doe': self.account_doe}
        self.homescreen = MagicMock(autospec='sakia.gui.homescreen.Homescreen')
        self.community_view = MagicMock(autospec='sakia.gui.community_view.CommunityView')
        self.password_asker = MagicMock(autospec='sakia.gui.password_asker.PasswordAsker')
        self.node_manager = MagicMock(autospec='sakia.gui.node_manager.NodeManager')

    def tearDown(self):
        self.tearDownQuamash()

    def test_change_account(self):
        widget = Mock(spec='PyQt5.QtWidgets.QMainWindow', create=True)
        widget.installEventFilter = Mock()
        ui = Mock(spec='sakia.gen_resources.mainwindow_uic.Ui_MainWindow', create=True)
        ui.setupUi = Mock()
        label_icon = Mock()
        label_status = Mock()
        label_time = Mock()
        combo_referentials = Mock()
        combo_referentials.currentIndexChanged = {str: Mock()}
        mainwindow = MainWindow(self.app, self.account_joe,
                                self.homescreen, self.community_view, self.node_manager,
                                widget, ui, label_icon,
                                label_status, label_time, combo_referentials, self.password_asker)
        mainwindow.refresh = Mock()
        mainwindow.action_change_account("doe")
        self.app.change_current_account.assert_called_once_with(self.account_doe)
        mainwindow.change_account()

        self.community_view.change_account.assert_called_once_with(self.account_doe, self.password_asker)
        self.password_asker.change_account.assert_called_once_with(self.account_doe)
        self.account_joe.contacts_changed.disconnect.assert_called_once_with(mainwindow.refresh_contacts)
        self.account_doe.contacts_changed.connect.assert_called_once_with(mainwindow.refresh_contacts)
        mainwindow.refresh.assert_called_once_with()

    def test_change_account_from_none(self):
        widget = Mock(spec='PyQt5.QtWidgets.QMainWindow', create=True)
        widget.installEventFilter = Mock()
        ui = Mock(spec='sakia.gen_resources.mainwindow_uic.Ui_MainWindow', create=True)
        ui.setupUi = Mock()
        label_icon = Mock()
        label_status = Mock()
        label_time = Mock()
        combo_referentials = Mock()
        combo_referentials.currentIndexChanged = {str: Mock()}

        type(self.app).current_account = PropertyMock(return_value=None)
        mainwindow = MainWindow(self.app, None, self.homescreen, self.community_view, self.node_manager,
                                widget, ui, label_icon,
                                label_status, label_time, combo_referentials, self.password_asker)
        mainwindow.refresh = Mock()
        mainwindow.action_change_account("doe")
        self.app.change_current_account.assert_called_once_with(self.account_doe)
        mainwindow.change_account()

        self.community_view.change_account.assert_called_once_with(self.account_doe, self.password_asker)
        self.password_asker.change_account.assert_called_once_with(self.account_doe)
        self.account_joe.contacts_changed.disconnect.assert_not_called()
        self.account_doe.contacts_changed.connect.assert_called_once_with(mainwindow.refresh_contacts)
        mainwindow.refresh.assert_called_once_with()