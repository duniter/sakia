import logging

from PyQt5.QtCore import QTime, pyqtSignal, QObject
from PyQt5.QtGui import QCursor

from sakia.decorators import asyncify, once_at_a_time
from sakia.gui.widgets import toast
from sakia.gui.widgets.context_menu import ContextMenu
from sakia.data.entities import Identity
from .model import TxHistoryModel
from .view import TxHistoryView
import attr


@attr.s()
class TxHistoryController(QObject):
    """
    Transfer history component controller
    """
    view_in_wot = pyqtSignal(object)

    view = attr.ib()
    model = attr.ib()
    password_asker = attr.ib()

    def __attrs_post_init__(self):
        """
        Init
        :param sakia.gui.txhistory.view.TxHistoryView view:
        :param sakia.gui.txhistory.model.TxHistoryModel model:
        :param password_asker:
        """
        super().__init__()
        ts_from, ts_to = self.view.get_time_frame()
        model = self.model.init_history_table_model(ts_from, ts_to)
        self.view.set_table_history_model(model)

        self.view.date_from.dateChanged['QDate'].connect(self.dates_changed)
        self.view.date_to.dateChanged['QDate'].connect(self.dates_changed)
        self.view.table_history.customContextMenuRequested['QPoint'].connect(self.history_context_menu)
        self.refresh()

    @classmethod
    def create(cls, parent, app, connection,
               identities_service, blockchain_service, transactions_service, sources_service):

        view = TxHistoryView(parent.view)
        model = TxHistoryModel(None, app, connection, blockchain_service, identities_service,
                               transactions_service, sources_service)
        txhistory = cls(view, model, None)
        model.setParent(txhistory)
        return txhistory

    def refresh_minimum_maximum(self):
        """
        Refresh minimum and maximum datetime
        """
        minimum, maximum = self.model.minimum_maximum_datetime()
        self.view.set_minimum_maximum_datetime(minimum, maximum)

    def refresh(self):
        self.refresh_minimum_maximum()
        self.refresh_balance()

    @asyncify
    async def notification_reception(self, received_list):
        if len(received_list) > 0:
            localized_amount = await self.model.received_amount(received_list)
            text = self.tr("Received {amount} from {number} transfers").format(amount=localized_amount,
                                                                           number=len(received_list))
            if self.model.notifications():
                toast.display(self.tr("New transactions received"), text)

    @once_at_a_time
    @asyncify
    async def refresh_balance(self):
        self.view.busy_balance.show()
        localized_amount = self.model.localized_balance()
        self.view.set_balance(localized_amount)
        self.view.busy_balance.hide()

    def history_context_menu(self, point):
        index = self.view.table_history.indexAt(point)
        valid, identity, transfer = self.model.table_data(index)
        if valid:
            if identity is None:
                if transfer.issuer != self.model.connection.pubkey:
                    pubkey = transfer.issuer
                else:
                    pubkey = transfer.receiver
                identity = Identity(currency=transfer.currency, pubkey=pubkey)
            menu = ContextMenu.from_data(self.view, self.model.app, self.model.connection, (identity, transfer))
            menu.view_identity_in_wot.connect(self.view_in_wot)

            # Show the context menu.
            menu.qmenu.popup(QCursor.pos())

    def dates_changed(self):
        logging.debug("Changed dates")
        if self.view.table_history.model():
            qdate_from = self.view.date_from
            qdate_from.setTime(QTime(0, 0, 0))
            qdate_to = self.view.date_to
            qdate_to.setTime(QTime(0, 0, 0))
            ts_from = qdate_from.dateTime().toTime_t()
            ts_to = qdate_to.dateTime().toTime_t()

            self.view.table_history.model().set_period(ts_from, ts_to)

            self.refresh_balance()
