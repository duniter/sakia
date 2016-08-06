import logging

from PyQt5.QtCore import QTime, pyqtSignal
from PyQt5.QtGui import QCursor

from ..component.controller import ComponentController
from .view import TxHistoryView
from .model import TxHistoryModel
from ...tools.decorators import asyncify, once_at_a_time
from ..widgets import toast
from ..widgets.context_menu import ContextMenu


class TxHistoryController(ComponentController):
    """
    Transfer history component controller
    """
    view_in_wot = pyqtSignal(object)

    def __init__(self, parent, view, model, password_asker=None):
        """
        Init
        :param sakia.gui.txhistory.view.TxHistoryView view:
        :param sakia.gui.txhistory.model.TxHistoryModel model:
        :param password_asker:
        """

        super().__init__(parent, view, model)
        self.password_asker = password_asker

        ts_from, ts_to = self.view.get_time_frame()
        model = self.model.init_history_table_model(ts_from, ts_to)
        self.view.set_table_history_model(model)

        self.view.date_from.dateChanged['QDate'].connect(self.dates_changed)
        self.view.date_to.dateChanged['QDate'].connect(self.dates_changed)
        self.view.table_history.customContextMenuRequested['QPoint'].connect(self.history_context_menu)
        self.model.loading_progressed.connect(self.view.set_progress_bar)
        self.refresh()

    @classmethod
    def create(cls, parent, app, **kwargs):
        account = kwargs['account']
        community = kwargs['community']

        view = TxHistoryView(parent.view)
        model = TxHistoryModel(None, app, account, community)
        txhistory = cls(parent, view, model)
        model.setParent(txhistory)
        return txhistory

    @once_at_a_time
    @asyncify
    async def refresh_minimum_maximum(self):
        """
        Refresh minimum and maximum datetime
        """
        minimum, maximum = await self.model.minimum_maximum_datetime()
        await self.view.set_minimum_maximum_datetime(minimum, maximum)

    def refresh(self):
        self.refresh_minimum_maximum()
        self.refresh_balance()

    @asyncify
    async def notification_reception(self, received_list):
        if len(received_list) > 0:
            localized_amount = await self.model.received_amount(received_list)
            text = self.tr("Received {amount} from {number} transfers").format(amount=localized_amount,
                                                                           number=len(received_list))
            if self.app.preferences['notifications']:
                toast.display(self.tr("New transactions received"), text)

    @once_at_a_time
    @asyncify
    async def refresh_balance(self):
        self.view.busy_balance.show()
        localized_amount = await self.model.localized_balance()
        self.view.set_balance(localized_amount)
        self.view.busy_balance.hide()

    @once_at_a_time
    @asyncify
    async def history_context_menu(self, point):
        index = self.view.table_history.indexAt(point)
        valid, identity, transfer = await self.model.table_data(index)
        if valid:
            menu = ContextMenu.from_data(self.view, self.model.app, self.model.account, self.model.community,
                                         self.password_asker,
                                         (identity, transfer))
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
