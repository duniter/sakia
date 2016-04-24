import logging

from duniterpy.api import errors
from PyQt5.QtWidgets import QWidget, QAbstractItemView, QHeaderView
from PyQt5.QtCore import Qt, QObject, QDateTime, QTime, QModelIndex, pyqtSignal, pyqtSlot, QEvent
from PyQt5.QtGui import QCursor

from ..gen_resources.transactions_tab_uic import Ui_transactionsTabWidget
from ..models.txhistory import HistoryTableModel, TxFilterProxyModel
from ..tools.exceptions import NoPeerAvailable
from ..tools.decorators import asyncify, once_at_a_time, cancel_once_task
from .widgets.context_menu import ContextMenu
from .widgets import toast


class TransactionsTabWidget(QObject):
    """
    classdocs
    """
    view_in_wot = pyqtSignal(object)

    def __init__(self, app, account=None, community=None, password_asker=None,
                 widget=QWidget, view=Ui_transactionsTabWidget):
        """
        Init

        :param sakia.core.app.Application app: Application instance
        :param sakia.core.Account account: The account displayed in the widget
        :param sakia.core.Community community: The community displayed in the widget
        :param sakia.gui.Password_Asker: password_asker: The widget to ask for passwords
        :param class widget: The class of the PyQt5 widget used for this tab
        :param class view: The class of the UI View for this tab
        """

        super().__init__()
        self.widget = widget()
        self.ui = view()
        self.ui.setupUi(self.widget)
        self.app = app
        self.account = account
        self.community = community
        self.password_asker = password_asker
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
        self.app.refresh_transfers.connect(self.refresh)

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
        except errors.duniterError as e:
            logging.debug(str(e))

    def refresh(self):
        if self.community:
            refresh_task = self.ui.table_history.model().sourceModel().refresh_transfers()
            refresh_task.add_done_callback(lambda fut: self.ui.table_history.resizeColumnsToContents())
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
    async def notification_reception(self, received_list):
        if len(received_list) > 0:
            amount = 0
            for r in received_list:
                amount += r.metadata['amount']
            localized_amount = await self.app.current_account.current_ref.instance(amount, self.community, self.app)\
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
        localized_amount = await self.app.current_account.current_ref.instance(amount, self.community,
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
            source_index = model.mapToSource(index)

            pubkey_col = model.sourceModel().columns_types.index('pubkey')
            pubkey_index = model.sourceModel().index(source_index.row(),
                                                    pubkey_col)
            pubkey = model.sourceModel().data(pubkey_index, Qt.DisplayRole)

            identity = await self.app.identities_registry.future_find(pubkey, self.community)

            transfer = model.sourceModel().transfers()[source_index.row()]
            menu = ContextMenu.from_data(self.widget, self.app, self.account, self.community, self.password_asker,
                                         (identity, transfer))
            menu.view_identity_in_wot.connect(self.view_in_wot)

            # Show the context menu.
            menu.qmenu.popup(QCursor.pos())

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
