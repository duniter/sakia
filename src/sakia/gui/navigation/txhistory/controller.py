import logging

from PyQt5.QtCore import QTime, pyqtSignal, QObject
from PyQt5.QtGui import QCursor

from sakia.decorators import asyncify
from sakia.gui.widgets import toast
from sakia.gui.widgets.context_menu import ContextMenu
from sakia.data.entities import Identity, Transaction
from .model import TxHistoryModel
from .view import TxHistoryView


class TxHistoryController(QObject):
    """
    Transfer history component controller
    """
    view_in_wot = pyqtSignal(object)

    def __init__(self, view, model):
        super().__init__()
        self.view = view
        self.model = model
        self._logger = logging.getLogger('sakia')
        ts_from, ts_to = self.view.get_time_frame()
        model = self.model.init_history_table_model(ts_from, ts_to)
        self.view.set_table_history_model(model)

        self.view.date_from.dateChanged.connect(self.dates_changed)
        self.view.date_to.dateChanged.connect(self.dates_changed)
        self.view.table_history.customContextMenuRequested['QPoint'].connect(self.history_context_menu)
        self.refresh()

    @classmethod
    def create(cls, parent, app, connection,
               identities_service, blockchain_service, transactions_service, sources_service):

        view = TxHistoryView(parent.view)
        model = TxHistoryModel(None, app, connection, blockchain_service, identities_service,
                               transactions_service, sources_service)
        txhistory = cls(view, model)
        model.setParent(txhistory)
        app.referential_changed.connect(txhistory.refresh_balance)
        app.sources_refreshed.connect(txhistory.refresh_balance)
        txhistory.view_in_wot.connect(lambda i: app.view_in_wot.emit(connection, i))
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

    def refresh_balance(self):
        localized_amount = self.model.localized_balance()
        self.view.set_balance(localized_amount)

    def history_context_menu(self, point):
        index = self.view.table_history.indexAt(point)
        valid, identity, transfer = self.model.table_data(index)
        if valid:
            if identity is None:
                if isinstance(transfer, Transaction):
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
        self._logger.debug("Changed dates")
        if self.view.table_history.model():
            qdate_from = self.view.date_from
            qdate_from.setTime(QTime(0, 0, 0))
            qdate_to = self.view.date_to
            qdate_to.setTime(QTime(0, 0, 0))
            ts_from = qdate_from.dateTime().toTime_t()
            ts_to = qdate_to.dateTime().toTime_t()

            self.view.table_history.model().set_period(ts_from, ts_to)

            self.refresh_balance()
