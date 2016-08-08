from sakia.gui.component.model import ComponentModel
from .table_model import HistoryTableModel, TxFilterProxyModel
from PyQt5.QtCore import Qt, QDateTime, QTime, pyqtSignal, QModelIndex
from sakia.tools.exceptions import NoPeerAvailable
from duniterpy.api import errors

import logging


class TxHistoryModel(ComponentModel):
    """
    The model of Navigation component
    """
    loading_progressed = pyqtSignal(int, int)

    def __init__(self, parent, app, account, community):
        """

        :param sakia.gui.txhistory.TxHistoryParent parent: the parent controller
        :param sakia.core.Application app: the app
        :param sakia.core.Account account: the account
        :param sakia.core.Community community: the community
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
        self._model = None
        self._proxy = None
        self.connect_progress()

    def init_history_table_model(self, ts_from, ts_to):
        """
        Generates a history table model
        :param int ts_from: date from where to filter tx
        :param int ts_to: date to where to filter tx
        :return:
        """
        self._model = HistoryTableModel(self.app, self.account, self.community)
        self._proxy = TxFilterProxyModel(ts_from, ts_to)
        self._proxy.setSourceModel(self._model)
        self._proxy.setDynamicSortFilter(True)
        self._proxy.setSortRole(Qt.DisplayRole)
        self._model.refresh_transfers()

        return self._proxy

    async def table_data(self, index):
        """
        Gets available table data at given index
        :param index:
        :return: tuple containing (Identity, Transfer)
        """
        if index.isValid() and index.row() < self.table_model.rowCount(QModelIndex()):
            source_index = self.table_model.mapToSource(index)

            pubkey_col = self.table_model.sourceModel().columns_types.index('pubkey')
            pubkey_index = self.table_model.sourceModel().index(source_index.row(),
                                                     pubkey_col)
            pubkey = self.table_model.sourceModel().data(pubkey_index, Qt.DisplayRole)

            identity = await self.app.identities_registry.future_find(pubkey, self.community)

            transfer = self.table_model.sourceModel().transfers()[source_index.row()]
            return True, identity, transfer
        return False, None, None

    def connect_progress(self):
        def progressing(community, value, maximum):
            if community == self.community:
                self.loading_progressed.emit(value, maximum)

        self.account.loading_progressed.connect(progressing)
        self.account.loading_finished.connect(self.stop_progress)

    def stop_progress(self, community, received_list):
        if community == self.community:
            self.loading_progressed.emit(100, 100)
            self.table_model.sourceModel().refresh_transfers()
            self.parent().notification_reception(received_list)

    async def minimum_maximum_datetime(self):
        """
        Get minimum and maximum datetime
        :rtype: Tuple[PyQt5.QtCore.QDateTime, PyQt5.QtCore.QDateTime]
        :return: minimum and maximum datetime
        """
        try:
            block = await self.community.get_block(1)
            minimum_datetime = QDateTime()
            minimum_datetime.setTime_t(block['medianTime'])
            minimum_datetime.setTime(QTime(0, 0))
            tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
            return minimum_datetime, tomorrow_datetime
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except errors.DuniterError as e:
            logging.debug(str(e))
        return QDateTime().currentDateTime(), QDateTime.currentDateTime().addDays(1)

    async def received_amount(self, received_list):
        """
        Converts a list of transactions to an amount
        :param list received_list:
        :return: the amount, localized
        """
        amount = 0
        for r in received_list:
            amount += r.metadata['amount']
        localized_amount = await self.app.current_account.current_ref.instance(amount, self.community, self.app) \
            .localized(units=True,
                       international_system=self.app.preferences['international_system_of_units'])
        return localized_amount

    async def localized_balance(self):
        """
        Get the localized amount of the given tx history
        :return: the localized amount of given account in given community
        :rtype: int
        """
        try:
            amount = await self.app.current_account.amount(self.community)
            localized_amount = await self.app.current_account.current_ref.instance(amount, self.community,
                                                       self.app).localized(units=True,
                                                                           international_system=
                                                                           self.app.preferences[
                                                                               'international_system_of_units'])
            return localized_amount
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except errors.DuniterError as e:
            logging.debug(str(e))
        return self.tr("Loading...")

    @property
    def table_model(self):
        return self._proxy
