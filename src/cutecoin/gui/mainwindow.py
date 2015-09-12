"""
Created on 1 févr. 2014

@author: inso
"""
from ..gen_resources.mainwindow_uic import Ui_MainWindow
from ..gen_resources.about_uic import Ui_AboutPopup

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QProgressBar, \
    QMessageBox, QLabel, QComboBox, QDialog, QApplication
from PyQt5.QtCore import QSignalMapper, pyqtSlot, QLocale, QEvent, \
    pyqtSlot, pyqtSignal, QDate, QDateTime, QTimer, QUrl, Qt, QCoreApplication
from PyQt5.QtGui import QIcon, QDesktopServices

from .process_cfg_account import ProcessConfigureAccount
from .transfer import TransferMoneyDialog
from .community_view import CommunityWidget
from .contact import ConfigureContactDialog
from .import_account import ImportAccountDialog
from .certification import CertificationDialog
from .password_asker import PasswordAskerDialog
from .preferences import PreferencesDialog
from .process_cfg_community import ProcessConfigureCommunity
from .homescreen import HomeScreenWidget
from ..core import money
from ..core.community import Community
from ..__init__ import __version__
from . import toast

import logging


class MainWindow(QMainWindow, Ui_MainWindow):
    """
    classdocs
    """

    def __init__(self, app):
        """
        Init
        :param cutecoin.core.app.Application app: application
        :type: cutecoin.core.app.Application
        """
        # Set up the user interface from Designer.
        super().__init__()
        self.app = app
        self.initialized = False
        self.password_asker = None
        self.import_dialog = None

        super().setupUi(self)

        QApplication.setWindowIcon(QIcon(":/icons/cutecoin_logo"))

        self.app.version_requested.connect(self.latest_version_requested)

        self.status_label = QLabel("", self)
        self.status_label.setTextFormat(Qt.RichText)
        self.statusbar.addPermanentWidget(self.status_label, 1)

        self.label_time = QLabel("", self)
        self.statusbar.addPermanentWidget(self.label_time)

        self.combo_referential = QComboBox(self)
        self.combo_referential.setEnabled(False)
        self.combo_referential.currentIndexChanged.connect(self.referential_changed)
        self.statusbar.addPermanentWidget(self.combo_referential)

        self.homescreen = HomeScreenWidget(self.app, self.status_label)
        self.homescreen.frame_communities.community_tile_clicked.connect(self.change_community)
        self.homescreen.toolbutton_new_account.addAction(self.action_add_account)
        self.homescreen.toolbutton_new_account.addAction(self.action_import)
        self.homescreen.button_add_community.clicked.connect(self.action_open_add_community)
        self.homescreen.button_disconnect.clicked.connect(lambda :self.action_change_account(""))
        self.centralWidget().layout().addWidget(self.homescreen)
        self.homescreen.toolbutton_connect.setMenu(self.menu_change_account)

        self.community_view = CommunityWidget(self.app, self.status_label)
        self.community_view.button_home.clicked.connect(lambda: self.change_community(None))
        self.community_view.button_certification.clicked.connect(self.open_certification_dialog)
        self.community_view.button_send_money.clicked.connect(self.open_transfer_money_dialog)
        self.centralWidget().layout().addWidget(self.community_view)

    def startup(self):
        self.update_time()
        self.app.get_last_version()
        if self.app.preferences['maximized']:
            self.showMaximized()
        else:
            self.show()
        if self.app.current_account:
            self.password_asker = PasswordAskerDialog(self.app.current_account)
            self.community_view.change_account(self.app.current_account, self.password_asker)
        self.refresh()

    def open_add_account_dialog(self):
        dialog = ProcessConfigureAccount(self.app, None)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.action_change_account(self.app.current_account.name)

    @pyqtSlot(str)
    def display_error(self, error):
        QMessageBox.critical(self, ":(",
                             error,
                             QMessageBox.Ok)

    @pyqtSlot(str)
    def referential_changed(self, index):
        if self.app.current_account:
            self.app.current_account.set_display_referential(index)
            if self.community_view:
                self.community_view.referential_changed()

    @pyqtSlot()
    def update_time(self):
        dateTime = QDateTime.currentDateTime()
        self.label_time.setText("{0}".format(QLocale.toString(
                        QLocale(),
                        QDateTime.currentDateTime(),
                        QLocale.dateTimeFormat(QLocale(), QLocale.NarrowFormat)
                    )))
        timer = QTimer()
        timer.timeout.connect(self.update_time)
        timer.start(1000)

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
        self.password_asker = PasswordAskerDialog(self.app.current_account)
        self.community_view.change_account(self.app.current_account, self.password_asker)
        self.refresh()

    @pyqtSlot()
    def action_open_add_community(self):
        dialog = ProcessConfigureCommunity(self.app,
                                           self.app.current_account, None,
                                           self.password_asker)
        if dialog.exec_() == QDialog.Accepted:
            self.app.save(self.app.current_account)
            dialog.community.start_coroutines()
            self.homescreen.refresh()

    def open_transfer_money_dialog(self):
        dialog = TransferMoneyDialog(self.app,
                                     self.app.current_account,
                                     self.password_asker)
        if dialog.exec_() == QDialog.Accepted:
            self.community_view.tab_history.table_history.model().sourceModel().refresh_transfers()

    def open_certification_dialog(self):
        dialog = CertificationDialog(self.app,
                                     self.app.current_account,
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

            if self.app.preferences['notifications']:
                toast.display("Cutecoin", """{version_info}""".format(
                version_info=version_info,
                version_url=version_url))

    @pyqtSlot(Community)
    def change_community(self, community):
        if self.community_view.community:
            self.community_view.community.stop_coroutines()

        if community:
            self.homescreen.hide()
            self.community_view.show()
        else:
            self.community_view.hide()
            self.homescreen.show()

        self.community_view.change_community(community)

    def refresh_accounts(self):
        self.menu_change_account.clear()
        for account_name in sorted(self.app.accounts.keys()):
            action = QAction(account_name, self)
            action.triggered.connect(lambda checked, account_name=account_name: self.action_change_account(account_name))
            self.menu_change_account.addAction(action)

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
        """
        Refresh main window
        When the selected account changes, all the widgets
        in the window have to be refreshed
        """
        logging.debug("Refresh started")
        self.refresh_accounts()
        self.homescreen.show()
        self.community_view.hide()
        self.homescreen.refresh()

        if self.app.current_account is None:
            self.setWindowTitle(self.tr("CuteCoin {0}").format(__version__))
            self.action_add_a_contact.setEnabled(False)
            self.actionCertification.setEnabled(False)
            self.actionTransfer_money.setEnabled(False)
            self.action_configure_parameters.setEnabled(False)
            self.action_set_as_default.setEnabled(False)
            self.menu_contacts_list.setEnabled(False)
            self.combo_referential.setEnabled(False)
            self.status_label.setText(self.tr(""))
            self.password_asker = None
        else:
            self.password_asker = PasswordAskerDialog(self.app.current_account)

            self.combo_referential.blockSignals(True)
            self.combo_referential.clear()
            for ref in money.Referentials:
                self.combo_referential.addItem(ref.translated_name())

            self.combo_referential.setEnabled(True)
            self.combo_referential.blockSignals(False)
            logging.debug(self.app.preferences)
            self.combo_referential.setCurrentIndex(self.app.preferences['ref'])
            self.action_add_a_contact.setEnabled(True)
            self.actionCertification.setEnabled(True)
            self.actionTransfer_money.setEnabled(True)
            self.menu_contacts_list.setEnabled(True)
            self.action_configure_parameters.setEnabled(True)
            self.setWindowTitle(self.tr("CuteCoin {0} - Account : {1}").format(__version__,
                                                                               self.app.current_account.name))

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
        export_dialog = QFileDialog(self)
        export_dialog.setObjectName('ExportFileDialog')
        export_dialog.setWindowTitle(self.tr("Export an account"))
        export_dialog.setNameFilter(self.tr("All account files (*.acc)"))
        export_dialog.setLabelText(QFileDialog.Accept, self.tr('Export'))
        export_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        export_dialog.accepted.connect(self.export_account_accepted)
        export_dialog.show()

    def export_account_accepted(self):
        export_dialog = self.sender()
        selected_file = export_dialog.selectedFiles()
        if selected_file:
            if selected_file[0][-4:] == ".acc":
                path = selected_file[0]
            else:
                path = selected_file[0] + ".acc"
            self.app.export_account(path, self.app.current_account)

    def closeEvent(self, event):
        self.app.stop()
        super().closeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super(MainWindow, self).changeEvent(event)

