'''
Created on 1 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.mainwindow_uic import Ui_MainWindow
from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QProgressBar, QMessageBox, QLabel, QDialog
from PyQt5.QtCore import QSignalMapper, QModelIndex, QObject, QThread, pyqtSlot, pyqtSignal
from PyQt5.QtGui import QIcon
from .process_cfg_account import ProcessConfigureAccount
from .transfer import TransferMoneyDialog
from .currency_tab import CurrencyTabWidget
from .add_contact import AddContactDialog
from .import_account import ImportAccountDialog
from .certification import CertificationDialog
from .password_asker import PasswordAskerDialog
from ..tools.exceptions import NoPeerAvailable
from ..__init__ import __version__
from cutecoin.gen_resources.about_uic import Ui_AboutPopup

import logging
import requests


class Loader(QObject):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.account_name = ""

    loaded = pyqtSignal()
    connection_error = pyqtSignal(str)

    def set_account_name(self, name):
        self.account_name = name

    @pyqtSlot()
    def load(self):
        if self.account_name != "":
            try:
                self.app.change_current_account(self.app.get_account(self.account_name))
            except requests.exceptions.RequestException as e:
                self.connection_error.emit(str(e))
                self.loaded.emit()

        self.loaded.emit()


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
        self.initialized = False
        self.busybar = QProgressBar(self.statusbar)
        self.busybar.setMinimum(0)
        self.busybar.setMaximum(0)
        self.busybar.setValue(-1)
        self.statusbar.addWidget(self.busybar)
        self.busybar.hide()

        self.status_label = QLabel("", self.statusbar)
        self.statusbar.addPermanentWidget(self.status_label)

        self.loader_thread = QThread()
        self.loader = Loader(self.app)
        self.loader.moveToThread(self.loader_thread)
        self.loader.loaded.connect(self.loader_finished)
        self.loader.loaded.connect(self.loader_thread.quit)
        self.loader.connection_error.connect(self.display_error)
        self.loader_thread.started.connect(self.loader.load)
        self.setWindowTitle("CuteCoin {0}".format(__version__))
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, None)
        dialog.accepted.connect(self.refresh)
        dialog.exec_()

    @pyqtSlot()
    def loader_finished(self):
        self.refresh()
        self.busybar.hide()

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

    def action_change_account(self, account_name):
        self.busybar.show()
        self.status_label.setText("Loading account {0}".format(account_name))
        self.loader.set_account_name(account_name)
        self.loader_thread.start(QThread.LowPriority)

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
        dialog.accepted.connect(self.refresh_communities)
        dialog.exec_()

    def open_about_popup(self):
        """
        Open about popup window
        """
        aboutDialog = QDialog(self)
        aboutUi = Ui_AboutPopup()
        aboutUi.setupUi(aboutDialog)
        text = """
        <h1>Cutecoin</h1>

        <p>Python/Qt uCoin client</p>

        <p>Version : {:}</p>

        <p>License : MIT</p>

        <p><b>Authors</b></p>

        <p>inso</p>
        <p>vit</p>
        <p>canercandan</p>
        """.format(__version__)
        aboutUi.label.setText(text)
        aboutDialog.show()

    def refresh_wallets(self):
        currency_tab = self.currencies_tabwidget.currentWidget()
        if currency_tab:
            currency_tab.refresh_wallets()

    def refresh_communities(self):
        self.currencies_tabwidget.clear()
        for community in self.app.current_account.communities:
            tab_currency = CurrencyTabWidget(self.app, community,
                                             self.password_asker,
                                             self.status_label)
            tab_currency.refresh()
            self.currencies_tabwidget.addTab(tab_currency,
                                             QIcon(":/icons/currency_icon"),
                                             community.name())

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

        for account_name in sorted(self.app.accounts.keys()):
            action = QAction(account_name, self)
            self.menu_change_account.addAction(action)
            signal_mapper.setMapping(action, account_name)
            action.triggered.connect(signal_mapper.map)
            signal_mapper.mapped[str].connect(self.action_change_account)

        if self.app.current_account is None:
            self.menu_contacts.setEnabled(False)
            self.menu_actions.setEnabled(False)
            self.action_configure_parameters.setEnabled(False)
            self.action_set_as_default.setEnabled(False)
        else:
            self.action_set_as_default.setEnabled(self.app.current_account.name
                                                  != self.app.default_account)
            self.password_asker = PasswordAskerDialog(self.app.current_account)
            self.menu_contacts.setEnabled(True)
            self.action_configure_parameters.setEnabled(True)
            self.menu_actions.setEnabled(True)
            self.setWindowTitle("CuteCoin {0} - Account : {1}".format(__version__,
                self.app.current_account.name))

            self.currencies_tabwidget.clear()
            for community in self.app.current_account.communities:
                try:
                    tab_currency = CurrencyTabWidget(self.app, community,
                                                     self.password_asker,
                                                     self.status_label)
                    tab_currency.refresh()
                    self.currencies_tabwidget.addTab(tab_currency,
                                                     QIcon(":/icons/currency_icon"),
                                                     community.name())
                except NoPeerAvailable as e:
                    QMessageBox.critical(self, "Could not join {0}".format(community.currency),
                                str(e),
                                QMessageBox.Ok)
                    continue
                except requests.exceptions.RequestException as e:
                    QMessageBox.critical(self, ":(",
                                str(e),
                                QMessageBox.Ok)

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
        self.loader.deleteLater()
        self.loader_thread.deleteLater()
        super().closeEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        if not self.initialized:
            if self.app.default_account != "":
                logging.debug("Loading default account")
                self.action_change_account(self.app.default_account)
            self.initialized = True
