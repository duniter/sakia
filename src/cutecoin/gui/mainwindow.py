'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog
from PyQt5.QtCore import QSignalMapper, QModelIndex, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from .process_cfg_account import ProcessConfigureAccount
from .transfer import TransferMoneyDialog
from .currency_tab import CurrencyTabWidget
from .add_contact import AddContactDialog
from .import_account import ImportAccountDialog
from .certification import CertificationDialog
from .password_asker import PasswordAskerDialog

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
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.password_asker = None
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, None)
        dialog.accepted.connect(self.refresh)
        dialog.exec_()

    def action_change_account(self, account_name):
        self.app.change_current_account(self.app.get_account(account_name))
        self.refresh()

    def open_transfer_money_dialog(self):
        dialog = TransferMoneyDialog(self.app.current_account,
                                     self.password_asker)
        dialog.accepted.connect(self.refresh_wallets)
        dialog.exec_()
        currency_tab = self.currencies_tabwidget.currentWidget()
        currency_tab.list_transactions_sent.model().dataChanged.emit(
                                                             QModelIndex(),
                                                             QModelIndex(), ())

    def open_certification_dialog(self):
        dialog = CertificationDialog(self.app.current_account,
                                     self.password_asker)
        dialog.exec_()

    def open_add_contact_dialog(self):
        AddContactDialog(self.app.current_account, self).exec_()

    def open_configure_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, self.app.current_account)
        dialog.accepted.connect(self.refresh_wallets)
        dialog.exec_()

    def refresh_wallets(self):
        currency_tab = self.currencies_tabwidget.currentWidget()
        currency_tab.refresh_wallets()

    def set_as_default_account(self):
        self.app.default_account = self.app.current_account.name
        logging.debug(self.app.current_account)
        self.app.save(self.app.current_account)
        self.action_set_as_default.setEnabled(False)

    '''
    Refresh main window
    When the selected account changes, all the widgets
    in the window have to be refreshed
    '''

    def refresh(self):
        self.menu_change_account.clear()
        signal_mapper = QSignalMapper(self)

        for account_name in self.app.accounts.keys():
            action = QAction(account_name, self)
            self.menu_change_account.addAction(action)
            signal_mapper.setMapping(action, account_name)
            action.triggered.connect(signal_mapper.map)
            signal_mapper.mapped[str].connect(self.action_change_account)

        if self.app.current_account is None:
            self.menu_contacts.setEnabled(False)
            self.menu_actions.setEnabled(False)
            self.action_set_as_default.setEnabled(False)
        else:
            self.action_set_as_default.setEnabled(self.app.current_account.name != self.app.default_account)
            self.password_asker = PasswordAskerDialog(self.app.current_account)
            self.menu_contacts.setEnabled(True)
            self.menu_actions.setEnabled(True)
            self.setWindowTitle("CuteCoin - Account : {0}".format(
                self.app.current_account.name))

            self.currencies_tabwidget.clear()
            for community in self.app.current_account.communities:
                tab_currency = CurrencyTabWidget(self.app, community, self.password_asker)
                tab_currency.refresh()
                self.currencies_tabwidget.addTab(tab_currency,
                                                 QIcon(":/icons/currency_icon"),
                                                 community.name())

            self.menu_contacts_list.clear()
            for contact in self.app.current_account.contacts:
                self.menu_contacts_list.addAction(contact.name)

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

    def closeEvent(self, event):
        if self.app.current_account:
            self.app.save_cache(self.app.current_account)
        super().closeEvent(event)

