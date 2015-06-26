'''
Created on 1 févr. 2014

@author: inso
'''
from ..gen_resources.mainwindow_uic import Ui_MainWindow
from ..gen_resources.about_uic import Ui_AboutPopup

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QProgressBar, \
    QMessageBox, QLabel, QComboBox, QDialog, QApplication
from PyQt5.QtCore import QSignalMapper, QObject, \
    pyqtSlot, pyqtSignal, QDate, QDateTime, QTimer, QUrl, Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QDesktopServices

from .process_cfg_account import ProcessConfigureAccount
from .transfer import TransferMoneyDialog
from .currency_tab import CurrencyTabWidget
from .contact import ConfigureContactDialog
from .import_account import ImportAccountDialog
from .certification import CertificationDialog
from .password_asker import PasswordAskerDialog
from .preferences import PreferencesDialog
from .homescreen import HomeScreenWidget
from ..core.account import Account
from ..__init__ import __version__
from . import toast

import logging


class MainWindow(QMainWindow, Ui_MainWindow):
    '''
    classdocs
    '''

    def __init__(self, app):
        """
        Init
        :param cutecoin.core.app.Application app: application
        :type: cutecoin.core.app.Application
        """
        # Set up the user interface from Designer.
        super().__init__()
        self.setupUi(self)
        QApplication.setWindowIcon(QIcon(":/icons/cutecoin_logo"))
        self.app = app

        self.app.load()
        self.initialized = False
        if self.app.preferences["account"] != "":
            account = self.app.get_account(self.app.preferences["account"])
            self.app.change_current_account(account)
        # no default account...
        else:
            # if at least one account exists, set it as default...
            if len(self.app.accounts) > 0:
                # capture names sorted alphabetically
                names = list(self.app.accounts.keys())
                names.sort()
                # set first name in list as default in preferences
                self.app.preferences['account'] = names[0]
                self.app.save_preferences(self.app.preferences)
                # open it
                logging.debug("No default account in preferences. Set %s as default account." % names[0])
                self.action_change_account(self.app.get_account(self.app.preferences['account']))

        self.password_asker = None

        self.busybar = QProgressBar(self.statusbar)
        self.busybar.setMinimum(0)
        self.busybar.setMaximum(0)
        self.busybar.setValue(-1)
        self.statusbar.addWidget(self.busybar)
        self.busybar.hide()
        self.app.version_requested.connect(self.latest_version_requested)
        self.app.get_last_version()

        self.combo_referential = QComboBox(self)
        self.combo_referential.setEnabled(False)
        self.combo_referential.currentIndexChanged.connect(self.referential_changed)

        self.status_label = QLabel("", self)
        self.status_label.setTextFormat(Qt.RichText)

        self.label_time = QLabel("", self)

        self.statusbar.addPermanentWidget(self.status_label, 1)
        self.statusbar.addPermanentWidget(self.label_time)
        self.statusbar.addPermanentWidget(self.combo_referential)
        self.update_time()

        self.homescreen = HomeScreenWidget(self.app)
        self.centralWidget().layout().addWidget(self.homescreen)
        self.homescreen.button_new.clicked.connect(self.open_add_account_dialog)
        self.homescreen.button_import.clicked.connect(self.import_account)
        self.open_ucoin_info = lambda: QDesktopServices.openUrl(QUrl("http://ucoin.io/theoretical/"))
        self.homescreen.button_info.clicked.connect(self.open_ucoin_info)

        self.import_dialog = None
        self.export_dialog = None

        # TODO: There are too much refresh() calls on startup
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, None)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.action_change_account(self.app.current_account)

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                             error,
                             QMessageBox.Ok)

    @pyqtSlot(str)
    def referential_changed(self, index):
        if self.app.current_account:
            self.app.current_account.set_display_referential(index)
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
        index = self.sender().data()
        dialog = ConfigureContactDialog(self.app.current_account, self, None, index)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    def action_change_account(self, account_name):
        self.app.change_current_account(self.app.get_account(account_name))
        self.refresh()

    @pyqtSlot()
    def loader_finished(self):
        logging.debug("Finished loading")
        self.refresh()
        self.busybar.hide()
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        try:
            self.app.disconnect()
        except:
            logging.debug("Disconnect of app failed")

        QApplication.processEvents()

    def open_transfer_money_dialog(self):
        dialog = TransferMoneyDialog(self.app.current_account,
                                     self.password_asker)
        dialog.accepted.connect(self.refresh_wallets)
        if dialog.exec_() == QDialog.Accepted:
            currency_tab = self.currencies_tabwidget.currentWidget()
            currency_tab.tab_history.table_history.model().sourceModel().refresh_transfers()

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
        result = dialog.exec_()
        if result == QDialog.Accepted:
            if self.app.current_account:
                self.action_change_account(self.app.current_account.name)
            else:
                self.refresh()

    def open_preferences_dialog(self):
        dialog = PreferencesDialog(self.app)
        result = dialog.exec_()

    def open_about_popup(self):
        """
        Open about popup window
        """
        aboutDialog = QDialog(self)
        aboutUi = Ui_AboutPopup()
        aboutUi.setupUi(aboutDialog)

        latest = self.app.available_version
        version_info = ""
        version_url = ""
        if not latest[0]:
            version_info = self.tr("Latest release : {version}") \
                .format(version=latest[1])
            version_url = latest[2]

            new_version_text = """
                <p><b>{version_info}</b></p>
                <p><a href="{version_url}">{link_text}</a></p>
                """.format(version_info=version_info,
                            version_url=version_url,
                            link_text=self.tr("Download link"))
        else:
            new_version_text = ""

        text = self.tr("""
        <h1>Cutecoin</h1>

        <p>Python/Qt uCoin client</p>

        <p>Version : {:}</p>
        {new_version_text}

        <p>License : MIT</p>

        <p><b>Authors</b></p>

        <p>inso</p>
        <p>vit</p>
        <p>canercandan</p>
        """).format(__version__, new_version_text=new_version_text)

        aboutUi.label.setText(text)
        aboutDialog.show()

    @pyqtSlot()
    def latest_version_requested(self):
        latest = self.app.available_version
        logging.debug("Latest version requested")
        if not latest[0]:
            version_info = self.tr("Please get the latest release {version}") \
                .format(version=latest[1])
            version_url = latest[2]

            toast.display("Cutecoin", """<p>{version_info}</br>
<a href={version_url}>Download link</a></p>""".format(
                version_info=version_info,
                version_url=version_url))

    def refresh_wallets(self):
        currency_tab = self.currencies_tabwidget.currentWidget()
        if currency_tab:
            currency_tab.refresh_wallets()

    def refresh_communities(self):
        logging.debug("CLEAR")
        self.currencies_tabwidget.clear()
        if self.app.current_account:
            for community in self.app.current_account.communities:
                tab_currency = CurrencyTabWidget(self.app, community,
                                                 self.password_asker,
                                                 self.status_label)
                tab_currency.refresh()
                self.currencies_tabwidget.addTab(tab_currency,
                                                 QIcon(":/icons/currency_icon"),
                                                 community.name)

    def refresh_accounts(self):
        self.menu_change_account.clear()
        signal_mapper = QSignalMapper(self)

        for account_name in sorted(self.app.accounts.keys()):
            action = QAction(account_name, self)
            self.menu_change_account.addAction(action)
            signal_mapper.setMapping(action, account_name)
            action.triggered.connect(signal_mapper.map)
            signal_mapper.mapped[str].connect(self.action_change_account)

    def refresh_contacts(self):
        self.menu_contacts_list.clear()
        if self.app.current_account:
            for index, contact in enumerate(self.app.current_account.contacts):
                contact_menu = self.menu_contacts_list.addMenu(contact['name'])
                edit_action = contact_menu.addAction(self.tr("Edit"))
                edit_action.triggered.connect(self.edit_contact)
                edit_action.setData(index)
                delete_action = contact_menu.addAction(self.tr("Delete"))
                delete_action.setData(contact)
                delete_action.triggered.connect(self.delete_contact)

    def refresh(self):
        '''
        Refresh main window
        When the selected account changes, all the widgets
        in the window have to be refreshed
        '''
        logging.debug("Refresh started")
        self.refresh_accounts()

        if self.app.current_account is None:
            self.currencies_tabwidget.hide()
            self.homescreen.show()
            self.setWindowTitle(self.tr("CuteCoin {0}").format(__version__))
            self.menu_account.setEnabled(False)
            self.action_configure_parameters.setEnabled(False)
            self.action_set_as_default.setEnabled(False)
            self.combo_referential.setEnabled(False)
            self.status_label.setText(self.tr(""))
            self.password_asker = None
        else:
            logging.debug("Show currencies loading")
            self.currencies_tabwidget.show()
            logging.debug("Hide homescreen")
            self.homescreen.hide()
            self.password_asker = PasswordAskerDialog(self.app.current_account)

            self.combo_referential.blockSignals(True)
            self.combo_referential.clear()
            for ref in self.app.current_account.referentials:
                self.combo_referential.addItem(QCoreApplication.translate('Account', ref[4]))

            self.combo_referential.setEnabled(True)
            self.combo_referential.blockSignals(False)
            logging.debug(self.app.preferences)
            self.combo_referential.setCurrentIndex(self.app.preferences['ref'])
            self.menu_account.setEnabled(True)
            self.action_configure_parameters.setEnabled(True)
            self.setWindowTitle(self.tr("CuteCoin {0} - Account : {1}").format(__version__,
                                                                               self.app.current_account.name))

        self.refresh_communities()
        self.refresh_wallets()
        self.refresh_contacts()

    def import_account(self):
        self.import_dialog = ImportAccountDialog(self.app, self)
        self.import_dialog.accepted.connect(self.import_account_accepted)
        self.import_dialog.exec_()

    def import_account_accepted(self):
        # open account after import
        self.action_change_account(self.import_dialog.edit_name.text())

    def export_account(self):
        # Testable way of using a QFileDialog
        self.export_dialog = QFileDialog(self)
        self.export_dialog.setObjectName('ExportFileDialog')
        self.export_dialog.setWindowTitle(self.tr("Export an account"))
        self.export_dialog.setNameFilter(self.tr("All account files (*.acc)"))
        self.export_dialog.setLabelText(QFileDialog.Accept, self.tr('Export'))
        self.export_dialog.accepted.connect(self.export_account_accepted)
        self.export_dialog.show()

    def export_account_accepted(self):
        selected_file = self.export_dialog.selectedFiles()
        if selected_file:
            if selected_file[0][-4:] == ".acc":
                path = selected_file[0]
            else:
                path = selected_file[0] + ".acc"
            self.app.export_account(path, self.app.current_account)

    def closeEvent(self, event):
        self.app.stop()
        super().closeEvent(event)

