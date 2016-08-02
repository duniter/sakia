import logging

from duniterpy.api import errors
from PyQt5.QtCore import QDateTime, QTime, pyqtSignal, QEvent

from ..component.controller import ComponentController
from .view import TxHistoryView
from .model import TxHistoryModel
from ...tools.exceptions import NoPeerAvailable
from ...tools.decorators import asyncify, once_at_a_time, cancel_once_task
from ..widgets import toast


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

        ts_from = self.view.date_from.dateTime().toTime_t()
        ts_to = self.view.date_to.dateTime().toTime_t()
        model = self.model.history_table_model(ts_from, ts_to)
        self.view.table_history.setModel(model)

        self.view.date_from.dateChanged['QDate'].connect(self.dates_changed)
        self.view.date_to.dateChanged['QDate'].connect(self.dates_changed)

        model.modelAboutToBeReset.connect(lambda: self.view.table_history.setEnabled(False))
        model.modelReset.connect(lambda: self.view.table_history.setEnabled(True))
        #self.app.refresh_transfers.connect(self.refresh)

        self.view.progressbar.hide()
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
        try:
            block = await self.community.get_block(1)
            minimum_datetime = QDateTime()
            minimum_datetime.setTime_t(block['medianTime'])
            minimum_datetime.setTime(QTime(0, 0))

            self.view.date_from.setMinimumDateTime(minimum_datetime)
            self.view.date_from.setDateTime(minimum_datetime)
            self.view.date_from.setMaximumDateTime(QDateTime().currentDateTime())

            self.view.date_to.setMinimumDateTime(minimum_datetime)
            tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
            self.view.date_to.setDateTime(tomorrow_datetime)
            self.view.date_to.setMaximumDateTime(tomorrow_datetime)
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except errors.DuniterError as e:
            logging.debug(str(e))

    def refresh(self):
        refresh_task = self.view.table_history.model().sourceModel().refresh_transfers()
        refresh_task.add_done_callback(lambda fut: self.view.table_history.resizeColumnsToContents())
        self.refresh_minimum_maximum()
        self.refresh_balance()

    def connect_progress(self):
        def progressing(community, value, maximum):
            if community == self.community:
                self.view.progressbar.show()
                self.view.progressbar.setValue(value)
                self.view.progressbar.setMaximum(maximum)
        self.account.loading_progressed.connect(progressing)
        self.account.loading_finished.connect(self.stop_progress)

    def stop_progress(self, community, received_list):
        if community == self.community:
            self.view.progressbar.hide()
            self.view.table_history.model().sourceModel().refresh_transfers()
            self.view.table_history.resizeColumnsToContents()
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
        self.view.busy_balance.show()
        try:
            amount = await self.app.current_account.amount(self.community)
            localized_amount = await self.app.current_account.current_ref.instance(amount, self.community,
                                                                           self.app).localized(units=True,
                                        international_system=self.app.preferences['international_system_of_units'])

            # set infos in label
            self.view.label_balance.setText(
                self.tr("{:}")
                .format(
                    localized_amount
                )
            )
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except errors.DuniterError as e:
            logging.debug(str(e))
        self.view.busy_balance.hide()

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

    def resizeEvent(self, event):
        self.view.busy_balance.resize(event.size())
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
        return super(TxHistoryController).changeEvent(event)
