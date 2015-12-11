import logging
import asyncio

from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QDialog, \
    QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QDateTime, QTime, QModelIndex, pyqtSignal, pyqtSlot, QEvent

from PyQt5.QtGui import QCursor

from ..gen_resources.certifications_tab_uic import Ui_certificationsTabWidget
from ..models.certifications import HistoryTableModel, CertsFilterProxyModel
from .contact import ConfigureContactDialog
from .member import MemberDialog
from .certification import CertificationDialog
from ..core.wallet import Wallet
from ..core.registry import Identity
from ..tools.exceptions import NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from .transfer import TransferMoneyDialog
from sakia.gui.widgets import toast
from sakia.gui.widgets.busy import Busy


class CertificationsTabWidget(QWidget, Ui_certificationsTabWidget):
    """
    classdocs
    """
    view_in_wot = pyqtSignal(Identity)

    def __init__(self, app):
        """
        Init

        :param sakia.core.app.Application app: Application instance
        :return:
        """

        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = None
        self.community = None
        self.password_asker = None
        self.busy_resume = Busy(self.groupbox_balance)
        self.busy_resume.hide()

        ts_from = self.date_from.dateTime().toTime_t()
        ts_to = self.date_to.dateTime().toTime_t()

        model = HistoryTableModel(self.app, self.account, self.community)
        proxy = CertsFilterProxyModel(ts_from, ts_to)
        proxy.setSourceModel(model)
        proxy.setDynamicSortFilter(True)
        proxy.setSortRole(Qt.DisplayRole)

        self.table_history.setModel(proxy)
        self.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_history.setSortingEnabled(True)
        self.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table_history.resizeColumnsToContents()

        model.modelAboutToBeReset.connect(lambda: self.table_history.setEnabled(False))
        model.modelReset.connect(lambda: self.table_history.setEnabled(True))

        self.progressbar.hide()
        self.refresh()

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_minimum_maximum)
        cancel_once_task(self, self.refresh_resume)
        cancel_once_task(self, self.history_context_menu)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()
        self.account = account
        self.password_asker = password_asker
        self.table_history.model().sourceModel().change_account(account)
        if account:
            self.connect_progress()

    def change_community(self, community):
        self.cancel_once_tasks()
        self.community = community
        self.progressbar.hide()
        self.table_history.model().sourceModel().change_community(self.community)
        self.refresh()

    @once_at_a_time
    @asyncify
    async def refresh_minimum_maximum(self):
        try:
            block = await self.community.get_block(1)
            minimum_datetime = QDateTime()
            minimum_datetime.setTime_t(block['medianTime'])
            minimum_datetime.setTime(QTime(0, 0))

            self.date_from.setMinimumDateTime(minimum_datetime)
            self.date_from.setDateTime(minimum_datetime)
            self.date_from.setMaximumDateTime(QDateTime().currentDateTime())

            self.date_to.setMinimumDateTime(minimum_datetime)
            tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
            self.date_to.setDateTime(tomorrow_datetime)
            self.date_to.setMaximumDateTime(tomorrow_datetime)
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except ValueError as e:
            logging.debug(str(e))

    def refresh(self):
        if self.community:
            self.table_history.model().sourceModel().refresh_transfers()
            self.table_history.resizeColumnsToContents()
            self.refresh_minimum_maximum()
            self.refresh_resume()

    def connect_progress(self):
        def progressing(community, value, maximum):
            if community == self.community:
                self.progressbar.show()
                self.progressbar.setValue(value)
                self.progressbar.setMaximum(maximum)
        self.account.loading_progressed.connect(progressing)
        self.account.loading_finished.connect(self.stop_progress)

    def stop_progress(self, community, received_list):
        if community == self.community:
            self.progressbar.hide()
            self.table_history.model().sourceModel().refresh_transfers()
            self.table_history.resizeColumnsToContents()
            self.notification_reception(received_list)

    @asyncify
    @asyncio.coroutine
    def notification_reception(self, received_list, sent_list):
        if len(received_list) > 0:
            text = self.tr("Received {nb_received} ; Sent {nb_sent}").format(nb_received=len(received_list) ,
                                                                            nb_sent=len(sent_list))
            if self.app.preferences['notifications']:
                toast.display(self.tr("New certifications"), text)

    @once_at_a_time
    @asyncify
    async def refresh_resume(self):
        self.busy_resume.show()
        self.busy_resume.hide()

    @once_at_a_time
    @asyncify
    async def history_context_menu(self, point):
        index = self.table_history.indexAt(point)
        model = self.table_history.model()
        if index.row() < model.rowCount(QModelIndex()):
            menu = QMenu(self.tr("Actions"), self)
            source_index = model.mapToSource(index)
            state_col = model.sourceModel().columns_types.index('state')
            state_index = model.sourceModel().index(source_index.row(),
                                                   state_col)
            state_data = model.sourceModel().data(state_index, Qt.DisplayRole)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                    pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)
            identity = await self.app.identities_registry.future_find(pubkey, self.community)

            if isinstance(identity, Identity):
                informations = QAction(self.tr("Informations"), self)
                informations.triggered.connect(self.menu_informations)
                informations.setData(identity)
                menu.addAction(informations)

                add_as_contact = QAction(self.tr("Add as contact"), self)
                add_as_contact.triggered.connect(self.menu_add_as_contact)
                add_as_contact.setData(identity)
                menu.addAction(add_as_contact)

            send_money = QAction(self.tr("Send money"), self)
            send_money.triggered.connect(self.menu_send_money)
            send_money.setData(identity)
            menu.addAction(send_money)

            if isinstance(identity, Identity):
                view_wot = QAction(self.tr("View in Web of Trust"), self)
                view_wot.triggered.connect(self.view_wot)
                view_wot.setData(identity)
                menu.addAction(view_wot)

            copy_pubkey = QAction(self.tr("Copy pubkey to clipboard"), self)
            copy_pubkey.triggered.connect(self.copy_pubkey_to_clipboard)
            copy_pubkey.setData(identity)
            menu.addAction(copy_pubkey)

            # Show the context menu.
            menu.popup(QCursor.pos())

    def copy_pubkey_to_clipboard(self):
        data = self.sender().data()
        clipboard = QApplication.clipboard()
        if data.__class__ is Wallet:
            clipboard.setText(data.pubkey)
        elif data.__class__ is Identity:
            clipboard.setText(data.pubkey)
        elif data.__class__ is str:
            clipboard.setText(data)

    def menu_informations(self):
        person = self.sender().data()
        self.identity_informations(person)

    def menu_add_as_contact(self):
        person = self.sender().data()
        self.add_identity_as_contact({'name': person.uid,
                                    'pubkey': person.pubkey})

    def menu_send_money(self):
        identity = self.sender().data()
        self.send_money_to_identity(identity)

    def identity_informations(self, person):
        dialog = MemberDialog(self.app, self.account, self.community, person)
        dialog.exec_()

    def add_identity_as_contact(self, person):
        dialog = ConfigureContactDialog(self.account, self.window(), person)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    @asyncify
    async def send_money_to_identity(self, identity):
        await TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        self.table_history.model().sourceModel().refresh_transfers()

    @asyncify
    async def certify_identity(self, identity):
        await CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    def view_wot(self):
        identity = self.sender().data()
        self.view_in_wot.emit(identity)

    def dates_changed(self):
        logging.debug("Changed dates")
        if self.table_history.model():
            qdate_from = self.date_from
            qdate_from.setTime(QTime(0, 0, 0))
            qdate_to = self.date_to
            qdate_to.setTime(QTime(0, 0, 0))
            ts_from = qdate_from.dateTime().toTime_t()
            ts_to = qdate_to.dateTime().toTime_t()

            self.table_history.model().set_period(ts_from, ts_to)

            self.refresh_resume()

    def resizeEvent(self, event):
        self.busy_resume.resize(event.size())
        super().resizeEvent(event)

    def changeEvent(self, event):
        """
        Intercepte LanguageChange event to translate UI
        :param QEvent QEvent: Event
        :return:
        """
        if event.type() == QEvent.LanguageChange:
            self.retranslateUi(self)
            self.refresh()
        return super(CertificationsTabWidget, self).changeEvent(event)
