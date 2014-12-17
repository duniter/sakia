'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog
from PyQt5.QtCore import QSignalMapper, QModelIndex
from cutecoin.gui.processConfigureAccount import ProcessConfigureAccount
from cutecoin.gui.transferMoneyDialog import TransferMoneyDialog
from cutecoin.gui.communityTabWidget import CommunityTabWidget
from cutecoin.gui.addContactDialog import AddContactDialog
from cutecoin.gui.importAccountDialog import ImportAccountDialog
from cutecoin.models.wallets import WalletsListModel
from cutecoin.models.sent import SentListModel
from cutecoin.models.received import ReceivedListModel

import logging


class MainWindow(QMainWindow, Ui_MainWindow):

    '''
    classdocs
    '''

    def __init__(self, app):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(MainWindow, self).__init__()
        self.setupUi(self)
        self.app = app
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, None)
        dialog.accepted.connect(self.refresh)
        dialog.exec_()

    def action_change_account(self, account_name):
        self.app.current_account = self.app.get_account(account_name)
        logging.info('Changing account to ' + self.app.current_account.name)
        self.refresh()

    def open_transfer_money_dialog(self):
        dialog = TransferMoneyDialog(self.app.current_account)
        dialog.accepted.connect(self.refresh_wallets)
        dialog.exec_()

    def open_add_contact_dialog(self):
        AddContactDialog(self.app.current_account, self).exec_()

    def open_configure_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, self.app.current_account)
        dialog.accepted.connect(self.refresh_wallets)
        dialog.exec_()

    '''
    Refresh main window
    When the selected account changes, all the widgets
    in the window have to be refreshed
    '''

    def refresh(self):
        self.menu_change_account.clear()
        signal_mapper = QSignalMapper(self)

        for account in self.app.accounts:
            action = QAction(account.name, self)
            self.menu_change_account.addAction(action)
            signal_mapper.setMapping(action, account.name)
            action.triggered.connect(signal_mapper.map)
            signal_mapper.mapped[str].connect(self.action_change_account)

        if self.app.current_account is None:
            self.tabs_account.setEnabled(False)
            self.menu_contacts.setEnabled(False)
            self.menu_actions.setEnabled(False)
        else:
            self.tabs_account.setEnabled(True)
            self.menu_contacts.setEnabled(True)
            self.menu_actions.setEnabled(True)
            self.label_account_name.setText(
                "Current account : " +
                self.app.current_account.name)

            self.refresh_wallets()

            self.tabs_communities.clear()
            for community in self.app.current_account.communities:
                tab_community = CommunityTabWidget(
                    self.app.current_account,
                    community)
                self.tabs_communities.addTab(tab_community, community.name())

            self.menu_contacts_list.clear()
            for contact in self.app.current_account.contacts:
                self.menu_contacts_list.addAction(contact.name)

            self.list_transactions_sent.setModel(
                SentListModel(
                    self.app.current_account))
            self.list_transactions_received.setModel(
                ReceivedListModel(
                    self.app.current_account))

    def refresh_wallets(self):
        wallets_list_model = WalletsListModel(self.app.current_account)
        self.list_wallets.setModel(wallets_list_model)
        self.refresh_wallet_content(QModelIndex())

    def refresh_wallet_content(self, index):
        pass

    def import_account(self):
        dialog = ImportAccountDialog(self.app, self)
        dialog.accepted.connect(self.refresh)
        dialog.exec_()

    def export_account(self):
        selected_file = QFileDialog.getSaveFileName(self,
                                          "Export an account",
                                          "",
                                          "All account files (*.acc)")
        path = ""
        if selected_file[0][-4:] == ".acc":
            path = selected_file[0]
        else:
            path = selected_file[0] + ".acc"
        self.app.export_account(path, self.app.current_account)
