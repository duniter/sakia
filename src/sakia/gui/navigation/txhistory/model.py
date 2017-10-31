from PyQt5.QtCore import QObject
from .table_model import HistoryTableModel
from PyQt5.QtCore import Qt, QDateTime, QTime, pyqtSignal, QModelIndex
from sakia.errors import NoPeerAvailable
from duniterpy.api import errors
from sakia.data.entities import Identity

import logging


class TxHistoryModel(QObject):
    """
    The model of Navigation component
    """
    def __init__(self, parent, app, connection, blockchain_service, identities_service,
                 transactions_service, sources_service):
        """

        :param sakia.gui.txhistory.TxHistoryParent parent: the parent controller
        :param sakia.app.Application app: the app
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        :param sakia.services.TransactionsService transactions_service: the identities service
        :param sakia.services.SourcesService sources_service: the sources service
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service
        self.transactions_service = transactions_service
        self.sources_service = sources_service
        self._model = None

    def init_history_table_model(self, ts_from, ts_to):
        """
        Generates a history table model
        :param int ts_from: date from where to filter tx
        :param int ts_to: date to where to filter tx
        :return:
        """
        self._model = HistoryTableModel(self, self.app, self.connection, ts_from, ts_to,
                                        self.identities_service, self.transactions_service)
        self._model.init_transfers()
        self.app.new_transfer.connect(self._model.init_transfers)
        self.app.new_dividend.connect(self._model.init_transfers)
        self.app.transaction_state_changed.connect(self._model.change_transfer)
        self.app.referential_changed.connect(self._model.modelReset)

        return self._model

    def change_page(self, page):
        self._model.set_current_page(page)

    def max_pages(self):
        return self._model.pages()

    def table_data(self, index):
        """
        Gets available table data at given index
        :param index:
        :return: tuple containing (Identity, Transfer)
        """
        if index.isValid() and index.row() < self.table_model.rowCount(QModelIndex()):
            pubkeys = self._model.pubkeys(index.row())
            identities_or_pubkeys = []
            for pubkey in pubkeys:
                identity = self.identities_service.get_identity(pubkey)
                if identity:
                    identities_or_pubkeys.append(identity)
                else:
                    identities_or_pubkeys.append(pubkey)
            transfer = self._model.transfers_data[index.row()][self._model.columns_types.index('raw_data')]
            return True,  identities_or_pubkeys, transfer
        return False, [], None

    def minimum_maximum_datetime(self):
        """
        Get minimum and maximum datetime
        :rtype: Tuple[PyQt5.QtCore.QDateTime, PyQt5.QtCore.QDateTime]
        :return: minimum and maximum datetime
        """
        minimum_datetime = QDateTime()
        minimum_datetime.setTime_t(1488322800) # First of may 2017
        tomorrow_datetime = QDateTime().currentDateTime().addDays(1)
        return minimum_datetime, tomorrow_datetime

    async def received_amount(self, received_list):
        """
        Converts a list of transactions to an amount
        :param list received_list:
        :return: the amount, localized
        """
        amount = 0
        for r in received_list:
            amount += r.metadata['amount']
        localized_amount = await self.app.current_ref.instance(amount,
                                                               self.connection.currency,
                                                               self.app).localized(True, True)
        return localized_amount

    def localized_balance(self):
        """
        Get the localized amount of the given tx history
        :return: the localized amount of given account in given community
        :rtype: int
        """
        try:
            amount = self.sources_service.amount(self.connection.pubkey)
            localized_amount = self.app.current_ref.instance(amount,
                                                             self.connection.currency,
                                                             self.app).localized(False, True)
            return localized_amount
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except errors.DuniterError as e:
            logging.debug(str(e))
        return self.tr("Loading...")

    @property
    def table_model(self):
        return self._model

    def notifications(self):
        return self.app.parameters.notifications
