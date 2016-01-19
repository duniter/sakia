import logging
import asyncio

from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView, QDialog, \
    QMenu, QAction, QApplication, QMessageBox
from PyQt5.QtCore import Qt, QObject, QDateTime, QTime, QModelIndex, pyqtSignal, pyqtSlot, QEvent
from PyQt5.QtGui import QCursor
from ucoinpy.documents import Block

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
from sakia.gui.widgets import toast
from sakia.gui.widgets.busy import Busy


class TransactionsTabWidget(QObject):
    """
    classdocs
    """
    view_in_wot = pyqtSignal(object)

    def __init__(self, app, widget=QWidget, view=Ui_transactionsTabWidget):
        """
        Init

        :param sakia.core.app.Application app: Application instance
        :return:
        """

        super().__init__()
        self.widget = widget()
        self.ui = view()
        self.ui.setupUi(self.widget)
        self.app = app
        self.account = None
        self.community = None
        self.password_asker = None
        self.ui.busy_balance.hide()

        ts_from = self.ui.date_from.dateTime().toTime_t()
        ts_to = self.ui.date_to.dateTime().toTime_t()
        model = HistoryTableModel(self.app, self.account, self.community)
        proxy = TxFilterProxyModel(ts_from, ts_to)
        proxy.setSourceModel(model)
        proxy.setDynamicSortFilter(True)
        proxy.setSortRole(Qt.DisplayRole)

        self.ui.table_history.setModel(proxy)
        self.ui.table_history.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.table_history.setSortingEnabled(True)
        self.ui.table_history.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.ui.table_history.resizeColumnsToContents()

        self.ui.table_history.customContextMenuRequested['QPoint'].connect(self.history_context_menu)
        self.ui.date_from.dateChanged['QDate'].connect(self.dates_changed)
        self.ui.date_to.dateChanged['QDate'].connect(self.dates_changed)

        model.modelAboutToBeReset.connect(lambda: self.ui.table_history.setEnabled(False))
        model.modelReset.connect(lambda: self.ui.table_history.setEnabled(True))

        self.ui.progressbar.hide()
        self.refresh()

    def cancel_once_tasks(self):
        cancel_once_task(self, self.refresh_minimum_maximum)
        cancel_once_task(self, self.refresh_balance)
        cancel_once_task(self, self.history_context_menu)

    def change_account(self, account, password_asker):
        self.cancel_once_tasks()
        self.account = account
        self.password_asker = password_asker
        self.ui.table_history.model().sourceModel().change_account(account)
        if account:
            self.connect_progress()

    def change_community(self, community):
        self.cancel_once_tasks()
        self.community = community
        self.ui.progressbar.hide()
        self.ui.table_history.model().sourceModel().change_community(self.community)
        self.refresh()

    @once_at_a_time
    @asyncify
    async def refresh_minimum_maximum(self):
        try:
            block = await self.community.get_block(1)
            minimum_datetime = QDateTime()
            minimum_datetime.setTime_t(block['medianTime'])
            minimum_datetime.setTime(QTime(0, 0))

            self.ui.date_from.setMinimumDateTime(minimum_datetime)
            self.ui.date_from.setDateTime(minimum_datetime)
            self.ui.date_from.setMaximumDateTime(QDateTime().currentDateTime())

            self.ui.date_to.setMinimumDateTime(minimum_datetime)
            tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
            self.ui.date_to.setDateTime(tomorrow_datetime)
            self.ui.date_to.setMaximumDateTime(tomorrow_datetime)
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except ValueError as e:
            logging.debug(str(e))

    def refresh(self):
        if self.community:
            self.ui.table_history.model().sourceModel().refresh_transfers()
            self.ui.table_history.resizeColumnsToContents()
            self.refresh_minimum_maximum()
            self.refresh_balance()

    def connect_progress(self):
        def progressing(community, value, maximum):
            if community == self.community:
                self.ui.progressbar.show()
                self.ui.progressbar.setValue(value)
                self.ui.progressbar.setMaximum(maximum)
        self.account.loading_progressed.connect(progressing)
        self.account.loading_finished.connect(self.stop_progress)

    def stop_progress(self, community, received_list):
        if community == self.community:
            self.ui.progressbar.hide()
            self.ui.table_history.model().sourceModel().refresh_transfers()
            self.ui.table_history.resizeColumnsToContents()
            self.notification_reception(received_list)

    @asyncify
    @asyncio.coroutine
    def notification_reception(self, received_list):
        if len(received_list) > 0:
            amount = 0
            for r in received_list:
                amount += r.metadata['amount']
            localized_amount = yield from self.app.current_account.current_ref(amount, self.community, self.app)\
                                            .localized(units=True,
                                    international_system=self.app.preferences['international_system_of_units'])
            text = self.tr("Received {amount} from {number} transfers").format(amount=localized_amount ,
                                                                            number=len(received_list))
            if self.app.preferences['notifications']:
                toast.display(self.tr("New transactions received"), text)

    @once_at_a_time
    @asyncify
    async def refresh_balance(self):
        self.ui.busy_balance.show()
        amount = await self.app.current_account.amount(self.community)
        localized_amount = await self.app.current_account.current_ref(amount, self.community,
                                                                           self.app).localized(units=True,
                                        international_system=self.app.preferences['international_system_of_units'])

        # set infos in label
        self.ui.label_balance.setText(
            self.tr("{:}")
            .format(
                localized_amount
            )
        )
        self.ui.busy_balance.hide()

    @once_at_a_time
    @asyncify
    async def history_context_menu(self, point):
        index = self.ui.table_history.indexAt(point)
        model = self.ui.table_history.model()
        if index.isValid() and index.row() < model.rowCount(QModelIndex()):
            menu = QMenu(self.tr("Actions"), self.widget)
            source_index = model.mapToSource(index)
            state_col = model.sourceModel().columns_types.index('state')
            state_index = model.sourceModel().index(source_index.row(),
                                                   state_col)
            state_data = model.sourceModel().data(state_index, Qt.DisplayRole)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                    pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)

            block_number_col = model.sourceModel().columns_types.index('block_number')
            block_number_index = model.sourceModel().index(source_index.row(),
                                                    block_number_col)
            block_number = model.sourceModel().data(block_number_index, Qt.DisplayRole)

            identity = await self.app.identities_registry.future_find(pubkey, self.community)

            transfer = model.sourceModel().transfers()[source_index.row()]
            if state_data == TransferState.REFUSED or state_data == TransferState.TO_SEND:
                send_back = QAction(self.tr("Send again"), self.widget)
                send_back.triggered.connect(lambda checked, tr=transfer: self.send_again(checked, tr))
                menu.addAction(send_back)

                cancel = QAction(self.tr("Cancel"), self.widget)
                cancel.triggered.connect(lambda checked, tr=transfer: self.cancel_transfer(tr))
                menu.addAction(cancel)
            else:
                if isinstance(identity, Identity):
                    informations = QAction(self.tr("Informations"), self.widget)
                    informations.triggered.connect(lambda checked, i=identity: self.menu_informations(i))
                    menu.addAction(informations)

                    add_as_contact = QAction(self.tr("Add as contact"), self.widget)
                    add_as_contact.triggered.connect(lambda checked,i=identity: self.menu_add_as_contact(i))
                    menu.addAction(add_as_contact)

                send_money = QAction(self.tr("Send money"), self.widget)
                send_money.triggered.connect(lambda checked, i=identity: self.menu_send_money(identity))
                menu.addAction(send_money)

                if isinstance(identity, Identity):
                    view_wot = QAction(self.tr("View in Web of Trust"), self.widget)
                    view_wot.triggered.connect(lambda checked, i=identity: self.view_wot(i))
                    menu.addAction(view_wot)

            copy_pubkey = QAction(self.tr("Copy pubkey to clipboard"), self.widget)
            copy_pubkey.triggered.connect(lambda checked, i=identity: self.copy_pubkey_to_clipboard(i))
            menu.addAction(copy_pubkey)

            if self.app.preferences['expert_mode']:
                if type(transfer) is Transfer:
                    copy_doc = QAction(self.tr("Copy raw transaction to clipboard"), self.widget)
                    copy_doc.triggered.connect(lambda checked, tx=transfer: self.copy_transaction_to_clipboard(tx))
                    menu.addAction(copy_doc)

                copy_doc = QAction(self.tr("Copy block to clipboard"), self.widget)
                copy_doc.triggered.connect(lambda checked, number=block_number: self.copy_block_to_clipboard(number))
                menu.addAction(copy_doc)

            # Show the context menu.
            menu.popup(QCursor.pos())

    def copy_pubkey_to_clipboard(self, identity):
        clipboard = QApplication.clipboard()
        clipboard.setText(identity.pubkey)

    @asyncify
    async def copy_transaction_to_clipboard(self, tx):
        clipboard = QApplication.clipboard()
        raw_doc = await tx.get_raw_document(self.community)
        clipboard.setText(raw_doc.signed_raw())

    @asyncify
    async def copy_block_to_clipboard(self, number):
        clipboard = QApplication.clipboard()
        block = await self.community.get_block(number)
        if block:
            block_doc = Block.from_signed_raw("{0}{1}\n".format(block['raw'], block['signature']))
            clipboard.setText(block_doc.signed_raw())

    def menu_informations(self, identity):
        dialog = MemberDialog(self.app, self.account, self.community, identity)
        dialog.exec_()

    def menu_add_as_contact(self, identity):
        dialog = ConfigureContactDialog(self.account, self.window(), identity)
        result = dialog.exec_()
        if result == QDialog.Accepted:
            self.window().refresh_contacts()

    @asyncify
    async def menu_send_money(self, identity):
        self.send_money_to_identity(identity)
        await TransferMoneyDialog.send_money_to_identity(self.app, self.account, self.password_asker,
                                                            self.community, identity)
        self.ui.table_history.model().sourceModel().refresh_transfers()

    @asyncify
    async def certify_identity(self, identity):
        await CertificationDialog.certify_identity(self.app, self.account, self.password_asker,
                                             self.community, identity)

    def view_wot(self, identity):
        self.view_in_wot.emit(identity)

    @asyncify
    async def send_again(self, checked=False, transfer=None):
        result = await TransferMoneyDialog.send_transfer_again(self.app, self.app.current_account,
                                     self.password_asker, self.community, transfer)
        self.ui.table_history.model().sourceModel().refresh_transfers()

    def cancel_transfer(self):
        reply = QMessageBox.warning(self, self.tr("Warning"),
                             self.tr("""Are you sure ?
This money transfer will be removed and not sent."""),
QMessageBox.Ok | QMessageBox.Cancel)
        if reply == QMessageBox.Ok:
            transfer = self.sender().data()
            transfer.cancel()
            self.ui.table_history.model().sourceModel().refresh_transfers()

    def dates_changed(self):
        logging.debug("Changed dates")
        if self.ui.table_history.model():
            qdate_from = self.ui.date_from
            qdate_from.setTime(QTime(0, 0, 0))
            qdate_to = self.ui.date_to
            qdate_to.setTime(QTime(0, 0, 0))
            ts_from = qdate_from.dateTime().toTime_t()
            ts_to = qdate_to.dateTime().toTime_t()

            self.ui.table_history.model().set_period(ts_from, ts_to)

            self.refresh_balance()

    def resizeEvent(self, event):
        self.ui.busy_balance.resize(event.size())
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
