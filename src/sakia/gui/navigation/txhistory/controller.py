import logging

from PyQt5.QtCore import QTime, pyqtSignal, QObject
from PyQt5.QtGui import QCursor

from sakia.decorators import asyncify
from sakia.gui.widgets import toast
from sakia.gui.widgets.context_menu import ContextMenu
from sakia.gui.sub.transfer.controller import TransferController
from .model import TxHistoryModel
from .view import TxHistoryView


class TxHistoryController(QObject):
    """
    Transfer history component controller
    """
    view_in_wot = pyqtSignal(object)

    def __init__(self, view, model, transfer):
        """

        :param TxHistoryView view:
        :param TxHistoryModel model:
        :param sakia.gui.sub.transfer.controller.TransferController transfer:
        """
        super().__init__()
        self.view = view
        self.model = model
        self.transfer = transfer
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

        transfer = TransferController.integrate_to_main_view(None, app, connection)
        view = TxHistoryView(parent.view, transfer.view)
        model = TxHistoryModel(None, app, connection, blockchain_service, identities_service,
                               transactions_service, sources_service)
        txhistory = cls(view, model, transfer)
        model.setParent(txhistory)
        app.referential_changed.connect(txhistory.refresh_balance)
        app.sources_refreshed.connect(txhistory.refresh_balance)
        txhistory.view_in_wot.connect(app.view_in_wot)
        txhistory.view.spin_page.valueChanged.connect(model.change_page)
        transfer.accepted.connect(view.clear)
        transfer.rejected.connect(view.clear)
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
        self.refresh_pages()

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

    def refresh_pages(self):
        pages = self.model.max_pages()
        self.view.set_max_pages(pages)

    def history_context_menu(self, point):
        index = self.view.table_history.indexAt(point)
        valid, identities, transfer = self.model.table_data(index)
        if valid:
            menu = ContextMenu.from_data(self.view, self.model.app, self.model.connection, identities + [transfer])
            menu.view_identity_in_wot.connect(self.view_in_wot)
            cursor = QCursor.pos()
            _x = cursor.x()
            _y = cursor.y()

            # Show the context menu.
            menu.qmenu.popup(cursor)

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
            self.refresh_pages()

