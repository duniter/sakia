import logging
import asyncio

from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QDialog, \
    QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QDateTime, QTime, QModelIndex, pyqtSignal, pyqtSlot, QEvent

from PyQt5.QtGui import QCursor

from ..gen_resources.transactions_tab_uic import Ui_transactionsTabWidget
from ..models.txhistory import HistoryTableModel, TxFilterProxyModel
from ..core.transfer import Transfer, TransferState
from .contact import ConfigureContactDialog
from .member import MemberDialog
from .certification import CertificationDialog
from ..core.wallet import Wallet
from ..core.registry import Identity
from ..tools.exceptions import NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from .transfer import TransferMoneyDialog
from cutecoin.gui.widgets import toast
from cutecoin.gui.widgets.busy import Busy


class TransactionsTabWidget(QWidget, Ui_transactionsTabWidget):
    """
    classdocs
    """
    view_in_wot = pyqtSignal(Identity)

    def __init__(self, app):
        """
        Init

        :param cutecoin.core.app.Application app: Application instance
        :return:
        """

        super().__init__()
        self.setupUi(self)
        self.app = app
        self.account = None
        self.community = None
        self.password_asker = None
        self.busy_balance = Busy(self.groupbox_balance)
        self.busy_balance.hide()

        ts_from = self.date_from.dateTime().toTime_t()
        ts_to = self.date_to.dateTime().toTime_t()
        model = HistoryTableModel(self.app, self.account, self.community)
        proxy = TxFilterProxyModel(ts_from, ts_to)
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
        cancel_once_task(self, self.refresh_balance)
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
    @asyncio.coroutine
    def refresh_minimum_maximum(self):
        try:
            block = yield from self.community.get_block(1)
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
        #TODO: Use resetmodel instead of destroy/create
        if self.community:
            self.table_history.model().sourceModel().refresh_transfers()
            self.table_history.resizeColumnsToContents()
            self.refresh_minimum_maximum()
            self.refresh_balance()

    def connect_progress(self):
        def progressing(community, value, maximum):
            if community == self.community:
                self.progressbar.show()
                self.progressbar.setValue(value)
                self.progressbar.setMaximum(maximum)
        self.app.current_account.loading_progressed.connect(progressing)
        self.app.current_account.loading_finished.connect(self.stop_progress)

    @pyqtSlot(list)
    def stop_progress(self, community, received_list):
        if community == self.community:
            amount = 0
            for r in received_list:
                amount += r.metadata['amount']
            self.progressbar.hide()
            if len(received_list) > 0:
                text = self.tr("Received {0} {1} from {2} transfers").format(amount,
                                                                   self.community.currency,
                                                                   len(received_list))
                if self.app.preferences['notifications']:
                    toast.display(self.tr("New transactions received"), text)

            self.table_history.model().sourceModel().refresh_transfers()
            self.table_history.resizeColumnsToContents()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def refresh_balance(self):
        self.busy_balance.show()
        amount = yield from self.app.current_account.amount(self.community)
        localized_amount = yield from self.app.current_account.current_ref(amount, self.community,
                                                                           self.app).localized(units=True,
                                        international_system=self.app.preferences['international_system_of_units'])

        # set infos in label
        self.label_balance.setText(
            self.tr("{:}")
            .format(
                localized_amount
            )
        )
        self.busy_balance.hide()

    @once_at_a_time
    @asyncify
    @asyncio.coroutine
    def history_context_menu(self, point):
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
            identity = yield from self.app.identities_registry.future_find(pubkey, self.community)

            transfer = model.sourceModel().transfers()[source_index.row()]
            if state_data == TransferState.REFUSED or state_data == TransferState.TO_SEND:
                send_back = QAction(self.tr("Send again"), self)
                send_back.triggered.connect(lambda checked, tr=transfer: self.send_again(checked, tr))
                send_back.setData(transfer)
                menu.addAction(send_back)

                cancel = QAction(self.tr("Cancel"), self)
                cancel.triggered.connect(self.cancel_transfer)
                cancel.setData(transfer)
                menu.addAction(cancel)
            else:
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
    @asyncio.coroutine
    def send_money_to_identity(self, identity):
        yield from TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        self.table_history.model().sourceModel().refresh_transfers()

    @asyncify
    @asyncio.coroutine
    def certify_identity(self, identity):
        yield from CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    def view_wot(self):
        identity = self.sender().data()
        self.view_in_wot.emit(identity)

    @asyncify
    @asyncio.coroutine
    def send_again(self, checked=False, transfer=None):
        result = yield from TransferMoneyDialog.send_transfer_again(self.app, self.app.current_account,
                                     self.password_asker, self.community, transfer)
        self.table_history.model().sourceModel().refresh_transfers()

    def cancel_transfer(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
This money transfer will be removed and not sent."""),
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transfer = self.sender().data()
            transfer.cancel()
            self.table_history.model().sourceModel().refresh_transfers()

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

            self.refresh_balance()

    def resizeEvent(self, event):
        self.busy_balance.resize(event.size())
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
        return super(TransactionsTabWidget, self).changeEvent(event)
