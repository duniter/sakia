'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QAction, QErrorMessage, QDialogButtonBox
from PyQt5.QtCore import QSignalMapper
from cutecoin.gui.processConfigureAccount import ProcessConfigureAccount
from cutecoin.gui.transferMoneyDialog import TransferMoneyDialog
from cutecoin.gui.communityTabWidget import CommunityTabWidget
from cutecoin.gui.addContactDialog import AddContactDialog
from cutecoin.models.account.wallets.listModel import WalletsListModel
from cutecoin.models.wallet.listModel import WalletListModel
from cutecoin.models.transaction.sentListModel import SentListModel
from cutecoin.models.transaction.receivedListModel import ReceivedListModel

import logging


class MainWindow(QMainWindow, Ui_MainWindow):

    '''
    classdocs
    '''

    def __init__(self, core):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.core = core
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.core, None)
        dialog.accepted.connect(self.refresh)
        dialog.exec_()

    def save(self):
        self.core.save()

    def action_change_account(self, account_name):
        self.core.current_account = self.core.get_account(account_name)
        logging.info('Changing account to ' + self.core.current_account.name)
        self.refresh()

    def open_transfer_money_dialog(self):
        TransferMoneyDialog(self.core.current_account).exec_()

    def open_add_contact_dialog(self):
        AddContactDialog(self.core.current_account, self).exec_()

    def open_configure_account_dialog(self):
        dialog = ProcessConfigureAccount(self.core, self.core.current_account)
        dialog.accepted.connect(self.refresh)
        dialog.exec_()

    '''
    Refresh main window
    When the selected account changes, all the widgets
    in the window have to be refreshed
    '''

    def refresh(self):
        self.menu_change_account.clear()
        signal_mapper = QSignalMapper(self)

        for account in self.core.accounts:
            action = QAction(account.name, self)
            self.menu_change_account.addAction(action)
            signal_mapper.setMapping(action, account.name)
            action.triggered.connect(signal_mapper.map)
            signal_mapper.mapped[str].connect(self.action_change_account)

        if self.core.current_account is None:
            self.tabs_account.setEnabled(False)
        else:
            self.tabs_account.setEnabled(True)
            self.label_account_name.setText(
                "Current account : " +
                self.core.current_account.name)
            self.list_wallets.setModel(
                WalletsListModel(
                    self.core.current_account))

            self.tabs_communities.clear()
            for community in self.core.current_account.communities:
                tab_community = CommunityTabWidget(
                    self.core.current_account,
                    community)
                quality = self.core.current_account.quality(community)
                self.tabs_communities.addTab(tab_community, quality +
                                                     " in " + community.name())

            self.menu_contacts_list.clear()
            for contact in self.core.current_account.contacts:
                self.menu_contacts_list.addAction(contact.name)

            self.list_transactions_sent.setModel(
                SentListModel(
                    self.core.current_account))
            self.list_transactions_received.setModel(
                ReceivedListModel(
                    self.core.current_account))

    def refresh_wallet_content(self, index):
        if index.isValid():
            current_wallet = self.core.current_account.wallets[index.row()]
            self.list_wallet_content.setModel(WalletListModel(current_wallet))
        else:
            self.list_wallet_content.setModel(WalletListModel([]))
