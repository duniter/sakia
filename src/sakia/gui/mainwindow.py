"""
Created on 1 févr. 2014

@author: inso
"""
import asyncio
import logging

from PyQt5.QtWidgets import QMainWindow, QAction, QFileDialog, QMessageBox, QLabel, QComboBox, QDialog, QApplication
from PyQt5.QtCore import QLocale, QEvent, \
    pyqtSlot, QDateTime, QTimer, Qt, QObject
from PyQt5.QtGui import QIcon

from ..gen_resources.mainwindow_uic import Ui_MainWindow
from ..gen_resources.about_uic import Ui_AboutPopup
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
from ..tools.decorators import asyncify
from ..__init__ import __version__
from .widgets import toast


class MainWindow(QObject):
    """
    classdocs
    """

    def __init__(self, app, homescreen, community_view, widget, ui,
                 label_icon, label_status, label_time, combo_referential,
                 password_asker):
        """
        Init
        :param sakia.core.app.Application app: application
        :param HomeScreenWidgetcreen homescreen: the homescreen
        :param CommunityView community_view: the community view
        :param QMainWindow widget: the widget of the main window
        :param Ui_MainWindow ui: the ui of the widget
        :param QLabel label_icon: the label of the icon in the statusbar
        :param QLabel label_status: the label of the status in the statusbar
        :param QLabel label_time: the label of the time in the statusbar
        :param QCombobox combo_referential: the combo of the referentials in the statusbar
        :param PasswordAsker password_asker: the password asker of the application
        :type: sakia.core.app.Application
        """
        # Set up the user interface from Designer.
        super().__init__()
        self.app = app
        self.initialized = False
        self.password_asker = password_asker
        self.import_dialog = None
        self.widget = widget
        self.ui = ui
        self.ui.setupUi(self.widget)
        self.widget.installEventFilter(self)

        QApplication.setWindowIcon(QIcon(":/icons/sakia_logo"))

        self.label_icon = label_icon

        self.status_label = label_status
        self.status_label.setTextFormat(Qt.RichText)

        self.label_time = label_time

        self.combo_referential = combo_referential
        self.combo_referential.setEnabled(False)
        self.combo_referential.currentIndexChanged.connect(self.referential_changed)

        self.homescreen = homescreen

        self.community_view = community_view

    def _init_ui(self):
        """
        Connects elements of the UI to the local slots
        """
        self.ui.statusbar.addPermanentWidget(self.label_icon, 1)
        self.ui.statusbar.addPermanentWidget(self.status_label, 2)
        self.ui.statusbar.addPermanentWidget(self.label_time)
        self.ui.statusbar.addPermanentWidget(self.combo_referential)

        self.ui.action_add_account.triggered.connect(self.open_add_account_dialog)
        self.ui.action_quit.triggered.connect(self.widget.close)
        self.ui.actionTransfer_money.triggered.connect(self.open_transfer_money_dialog)
        self.ui.action_add_a_contact.triggered.connect(self.open_add_contact_dialog)
        self.ui.action_configure_parameters.triggered.connect(self.open_configure_account_dialog)
        self.ui.action_import.triggered.connect(self.import_account)
        self.ui.action_export.triggered.connect(self.export_account)
        self.ui.actionCertification.triggered.connect(self.open_certification_dialog)
        self.ui.actionPreferences.triggered.connect(self.open_preferences_dialog)
        self.ui.actionAbout.triggered.connect(self.open_about_popup)

    def _init_homescreen(self):
        """
        Initialize homescreen signals/slots and data
        :return:
        """
        self.homescreen.status_label = self.status_label
        self.homescreen.frame_communities.community_tile_clicked.connect(self.change_community)
        self.homescreen.toolbutton_new_account.clicked.connect(self.open_add_account_dialog)
        self.homescreen.toolbutton_new_account.addAction(self.ui.action_add_account)
        self.homescreen.toolbutton_new_account.addAction(self.ui.action_import)
        self.homescreen.button_add_community.clicked.connect(self.action_open_add_community)
        self.homescreen.button_disconnect.clicked.connect(lambda :self.action_change_account(""))
        self.widget.centralWidget().layout().addWidget(self.homescreen)
        self.homescreen.toolbutton_connect.setMenu(self.ui.menu_change_account)

    def _init_community_view(self):
        """
        Initialize the community view signals/slots and data
        :return:
        """
        self.community_view.status_label = self.status_label
        self.community_view.label_icon = self.label_icon
        self.community_view.button_home.clicked.connect(lambda: self.change_community(None))
        self.community_view.button_certification.clicked.connect(self.open_certification_dialog)
        self.community_view.button_send_money.clicked.connect(self.open_transfer_money_dialog)
        self.widget.centralWidget().layout().addWidget(self.community_view)

    @classmethod
    def startup(cls, app):
        qmainwindow = QMainWindow()
        main_window = cls(app, HomeScreenWidget(app, None),
                          CommunityWidget(app, None, None),
                          qmainwindow, Ui_MainWindow(),
                          QLabel("", qmainwindow), QLabel("", qmainwindow),
                          QLabel("", qmainwindow), QComboBox(qmainwindow),
                          PasswordAskerDialog(None))
        app.version_requested.connect(main_window.latest_version_requested)
        app.account_imported.connect(main_window.import_account_accepted)
        main_window._init_ui()
        main_window._init_homescreen()
        main_window._init_community_view()

        main_window.update_time()
        # FIXME : Need python 3.5 self.app.get_last_version()
        if app.preferences['maximized']:
            main_window.widget.showMaximized()
        else:
            main_window.widget.show()
        if app.current_account:
            main_window.password_asker = PasswordAskerDialog(app.current_account)
            main_window.community_view.change_account(app.current_account, main_window.password_asker)
            main_window.app.current_account.contacts_changed.connect(main_window.refresh_contacts)
        main_window.refresh()

    @asyncify
    async def open_add_account_dialog(self, checked=False):
        dialog = ProcessConfigureAccount(self.app, None)
        result = await dialog.async_exec()
        if result == QDialog.Accepted:
            self.action_change_account(self.app.current_account.name)

    @asyncify
    async def open_configure_account_dialog(self, checked=False):
        dialog = ProcessConfigureAccount(self.app, self.app.current_account)
        result = await dialog.async_exec()
        if result == QDialog.Accepted:
            if self.app.current_account:
                self.action_change_account(self.app.current_account.name)
            else:
                self.refresh()

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
                self.homescreen.referential_changed()

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
        self.app.current_account.remove_contacts(contact)

    @pyqtSlot()
    def edit_contact(self):
        index = self.sender().data()
        dialog = ConfigureContactDialog(self.app, self.app.current_account, self, None, index)
        dialog.exec_()

    def action_change_account(self, account_name):
        if self.app.current_account:
            self.app.current_account.contacts_changed.disconnect(self.refresh_contacts)
        self.app.change_current_account(self.app.get_account(account_name))
        self.password_asker.change_account(self.app.current_account)
        self.community_view.change_account(self.app.current_account, self.password_asker)
        if self.app.current_account:
            self.app.current_account.contacts_changed.connect(self.refresh_contacts)
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
                                     self.password_asker,
                                     self.community_view.community,
                                     None)
        if dialog.exec() == QDialog.Accepted:
            self.community_view.tab_history.table_history.model().sourceModel().refresh_transfers()

    def open_certification_dialog(self):
        CertificationDialog.open_dialog(self.app,
                                     self.app.current_account,
                                     self.password_asker)

    def open_add_contact_dialog(self):
        dialog = ConfigureContactDialog(self.app, self.app.current_account, self)
        dialog.exec_()

    def open_preferences_dialog(self):
        dialog = PreferencesDialog(self.app)
        dialog.exec_()

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
        <h1>sakia</h1>

        <p>Python/Qt uCoin client</p>

        <p>Version : {:}</p>
        {new_version_text}

        <p>License : GPLv3</p>

        <p><b>Authors</b></p>

        <p>inso</p>
        <p>vit</p>
        <p>Moul</p>
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
                toast.display("sakia", """{version_info}""".format(
                version_info=version_info,
                version_url=version_url))

    @pyqtSlot(Community)
    def change_community(self, community):
        if community:
            self.homescreen.hide()
            self.community_view.show()
        else:
            self.community_view.hide()
            self.homescreen.show()

        self.community_view.change_community(community)

    def refresh_accounts(self):
        self.ui.menu_change_account.clear()
        for account_name in sorted(self.app.accounts.keys()):
            action = QAction(account_name, self.widget)
            action.triggered.connect(lambda checked, account_name=account_name: self.action_change_account(account_name))
            self.ui.menu_change_account.addAction(action)

    def refresh_contacts(self):
        self.ui.menu_contacts_list.clear()
        if self.app.current_account:
            for index, contact in enumerate(self.app.current_account.contacts):
                contact_menu = self.ui.menu_contacts_list.addMenu(contact['name'])
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
        self.community_view.hide()
        self.homescreen.show()
        self.homescreen.refresh()

        if self.app.current_account is None:
            self.widget.setWindowTitle(self.tr("sakia {0}").format(__version__))
            self.ui.action_add_a_contact.setEnabled(False)
            self.ui.actionCertification.setEnabled(False)
            self.ui.actionTransfer_money.setEnabled(False)
            self.ui.action_configure_parameters.setEnabled(False)
            self.ui.action_set_as_default.setEnabled(False)
            self.ui.menu_contacts_list.setEnabled(False)
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
            self.ui.action_add_a_contact.setEnabled(True)
            self.ui.actionCertification.setEnabled(True)
            self.ui.actionTransfer_money.setEnabled(True)
            self.ui.menu_contacts_list.setEnabled(True)
            self.ui.action_configure_parameters.setEnabled(True)
            self.widget.setWindowTitle(self.tr("sakia {0} - Account : {1}").format(__version__,
                                                                               self.app.current_account.name))

        self.refresh_contacts()

    def import_account(self):
        import_dialog = ImportAccountDialog(self.app, self)
        import_dialog.exec_()

    def import_account_accepted(self, account_name):
        # open account after import
        self.action_change_account(account_name)

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

    def eventFilter(self, target, event):
        """
        Event filter on the widget
        :param QObject target: the target of the event
        :param QEvent event: the event
        :return: bool
        """
        if target == self.widget:
            if event.type() == QEvent.Close:
                self.app.stop()
            if event.type() == QEvent.LanguageChange:
                self.ui.retranslateUi(self)
                self.refresh()
            return self.widget.eventFilter(target, event)
        return False

