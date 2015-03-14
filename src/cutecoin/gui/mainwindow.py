'''
Created on 1 févr. 2014

@author: inso
'''
from ..gen_resources.mainwindow_uic import Ui_MainWindow
from ..gen_resources.about_uic import Ui_AboutPopup
from ..gen_resources.homescreen_uic import Ui_HomeScreenWidget

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QProgressBar, \
        QMessageBox, QLabel, QComboBox, QDialog
from PyQt5.QtCore import QSignalMapper, QObject, QThread, \
    pyqtSlot, pyqtSignal, QDate, QDateTime, QTimer, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices

from .process_cfg_account import ProcessConfigureAccount
from .transfer import TransferMoneyDialog
from .currency_tab import CurrencyTabWidget
from .contact import ConfigureContactDialog
from .import_account import ImportAccountDialog
from .certification import CertificationDialog
from .password_asker import PasswordAskerDialog
from ..tools.exceptions import NoPeerAvailable
from .homescreen import HomeScreenWidget
from ..core.account import Account
from ..__init__ import __version__

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
                account = self.app.get_account(self.account_name)
                self.app.change_current_account(account)
            except requests.exceptions.RequestException as e:
                self.connection_error.emit(str(e))
                self.loaded.emit()
            except NoPeerAvailable as e:
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

        self.combo_referential = QComboBox(self)
        self.combo_referential.setEnabled(False)
        self.combo_referential.currentTextChanged.connect(self.referential_changed)

        self.status_label = QLabel("", self)

        self.label_time = QLabel("", self)

        self.statusbar.addPermanentWidget(self.status_label, 1)
        self.statusbar.addPermanentWidget(self.label_time)
        self.statusbar.addPermanentWidget(self.combo_referential)
        self.update_time()

        self.loader_thread = QThread()
        self.loader = Loader(self.app)
        self.loader.moveToThread(self.loader_thread)
        self.loader.loaded.connect(self.loader_finished)
        self.loader.loaded.connect(self.loader_thread.quit)
        self.loader.connection_error.connect(self.display_error)
        self.loader_thread.started.connect(self.loader.load)

        self.homescreen = HomeScreenWidget()
        self.centralWidget().layout().addWidget(self.homescreen)
        self.homescreen.button_new.clicked.connect(self.open_add_account_dialog)
        self.homescreen.button_import.clicked.connect(self.import_account)
        self.open_ucoin_info = lambda: QDesktopServices.openUrl(QUrl("http://ucoin.io/theoretical/"))
        self.homescreen.button_info.clicked.connect(self.open_ucoin_info)

        #TODO: There are too much refresh() calls on startup
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, None)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.action_change_account(self.app.current_account.name)

    @pyqtSlot()
    def loader_finished(self):
        self.refresh()
        self.busybar.hide()
        self.app.disconnect()

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                    error,
                    QMessageBox.Ok)

    @pyqtSlot(str)
    def referential_changed(self, text):
        if self.app.current_account:
            self.app.current_account.set_display_referential(text)
            if self.currencies_tabwidget.currentWidget():
                self.currencies_tabwidget.currentWidget().referential_changed()

    @pyqtSlot()
    def update_time(self):
        date = QDate.currentDate()
        self.label_time.setText("{0}".format(date.toString("dd/MM/yyyy")))
        next_day = date.addDays(1)
        current_time = QDateTime().currentDateTime().toMSecsSinceEpoch()
        next_time = QDateTime(next_day).toMSecsSinceEpoch()
        timer = QTimer()
        timer.timeout.connect(self.update_time)
        timer.start(next_time - current_time)

    @pyqtSlot()
    def delete_contact(self):
        contact = self.sender().data()
        self.app.current_account.contacts.remove(contact)
        self.refresh_contacts()

    @pyqtSlot()
    def edit_contact(self):
        contact = self.sender().data()
        dialog = ConfigureContactDialog(self.app.current_account, self, contact, True)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def action_change_account(self, account_name):
        def loading_progressed(value, maximum):
            logging.debug("Busybar : {:} : {:}".format(value, maximum))
            self.busybar.setValue(value)
            self.busybar.setMaximum(maximum)
        self.app.loading_progressed.connect(loading_progressed)
        self.busybar.show()
        self.status_label.setText("Loading account {0}".format(account_name))
        self.loader.set_account_name(account_name)
        self.loader_thread.start(QThread.LowPriority)
        self.homescreen.setEnabled(False)

    def open_transfer_money_dialog(self):
        dialog = TransferMoneyDialog(self.app.current_account,
                                     self.password_asker)
        dialog.accepted.connect(self.refresh_wallets)
        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.currencies_tabwidget.currentWidget()
            currency_tab.table_history.model().invalidate()

    def open_certification_dialog(self):
        dialog = CertificationDialog(self.app.current_account,
                                     self.password_asker)
        dialog.exec_()

    def open_add_contact_dialog(self):
        dialog = ConfigureContactDialog(self.app.current_account, self)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def open_configure_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, self.app.current_account)
        dialog.accepted.connect(self.refresh)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.action_change_account(self.app.current_account.name)

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
        if self.app.current_account:
            for community in self.app.current_account.communities:
                try:
                    tab_currency = CurrencyTabWidget(self.app, community,
                                                     self.password_asker,
                                                     self.status_label)
                    tab_currency.refresh()
                    self.currencies_tabwidget.addTab(tab_currency,
                                                     QIcon(":/icons/currency_icon"),
                                                     community.name)
                except NoPeerAvailable as e:
                    QMessageBox.critical(self, "Could not join {0}".format(community.currency),
                                str(e),
                                QMessageBox.Ok)
                    continue
                except requests.exceptions.RequestException as e:
                    QMessageBox.critical(self, ":(",
                                str(e),
                                QMessageBox.Ok)

    def refresh_contacts(self):
        self.menu_contacts_list.clear()
        if self.app.current_account:
            for contact in self.app.current_account.contacts:
                contact_menu = self.menu_contacts_list.addMenu(contact.name)
                edit_action = contact_menu.addAction("Edit")
                edit_action.triggered.connect(self.edit_contact)
                edit_action.setData(contact)
                delete_action = contact_menu.addAction("Delete")
                delete_action.setData(contact)
                delete_action.triggered.connect(self.delete_contact)

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
        logging.debug("Refresh finished")
        self.menu_change_account.clear()
        signal_mapper = QSignalMapper(self)

        for account_name in sorted(self.app.accounts.keys()):
            action = QAction(account_name, self)
            self.menu_change_account.addAction(action)
            signal_mapper.setMapping(action, account_name)
            action.triggered.connect(signal_mapper.map)
            signal_mapper.mapped[str].connect(self.action_change_account)

        if self.app.current_account is None:
            self.currencies_tabwidget.hide()
            self.homescreen.show()
            self.setWindowTitle("CuteCoin {0}".format(__version__))
            self.menu_contacts.setEnabled(False)
            self.menu_actions.setEnabled(False)
            self.action_configure_parameters.setEnabled(False)
            self.action_set_as_default.setEnabled(False)
            self.combo_referential.setEnabled(False)
            self.status_label.setText("")
            self.password_asker = None
        else:
            self.currencies_tabwidget.show()
            self.homescreen.hide()
            self.action_set_as_default.setEnabled(self.app.current_account.name
                                                  != self.app.default_account)
            self.password_asker = PasswordAskerDialog(self.app.current_account)

            self.combo_referential.blockSignals(True)
            self.combo_referential.clear()
            self.combo_referential.addItems(sorted(Account.referentials.keys()))
            self.combo_referential.setEnabled(True)
            self.combo_referential.blockSignals(False)
            self.combo_referential.setCurrentText(self.app.current_account.referential)
            self.menu_contacts.setEnabled(True)
            self.action_configure_parameters.setEnabled(True)
            self.menu_actions.setEnabled(True)
            self.password_asker = PasswordAskerDialog(self.app.current_account)
            self.setWindowTitle("CuteCoin {0} - Account : {1}".format(__version__,
                self.app.current_account.name))

        self.refresh_communities()
        self.refresh_wallets()
        self.refresh_contacts()

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
        self.app.save_persons()
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
