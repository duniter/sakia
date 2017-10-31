import datetime
import logging

from PyQt5.QtCore import QAbstractTableModel, Qt, QVariant, QSortFilterProxyModel, \
    QDateTime, QLocale, QModelIndex, QT_TRANSLATE_NOOP
from PyQt5.QtGui import QFont, QColor
from sakia.data.entities import Transaction
from sakia.constants import MAX_CONFIRMATIONS
from sakia.data.processors import BlockchainProcessor
from .sql_adapter import TxHistorySqlAdapter
from sakia.data.repositories import TransactionsRepo, DividendsRepo


class HistoryTableModel(QAbstractTableModel):
    """
    A Qt abstract item model to display communities in a tree
    """

    DIVIDEND = 32

    columns_types = (
        'date',
        'pubkey',
        'amount',
        'comment',
        'state',
        'txid',
        'pubkey',
        'block_number',
        'txhash',
        'raw_data'
    )

    columns_to_sql = {
        'date': "ts",
        "pubkey": "pubkey",
        "amount": "amount",
        "comment": "comment"
    }

    columns_headers = (
        QT_TRANSLATE_NOOP("HistoryTableModel", 'Date'),
        QT_TRANSLATE_NOOP("HistoryTableModel", 'Public key'),
        QT_TRANSLATE_NOOP("HistoryTableModel", 'Amount'),
        QT_TRANSLATE_NOOP("HistoryTableModel", 'Comment')
    )

    def __init__(self, parent, app, connection, ts_from, ts_to,  identities_service, transactions_service):
        """
        History of all transactions
        :param PyQt5.QtWidgets.QWidget parent: parent widget
        :param sakia.app.Application app: the main application
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.services.IdentitiesService identities_service: the identities service
        :param sakia.services.TransactionsService transactions_service: the transactions service
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.blockchain_processor = BlockchainProcessor.instanciate(app)
        self.identities_service = identities_service
        self.sql_adapter = TxHistorySqlAdapter(self.app.db.conn)
        self.transactions_repo = TransactionsRepo(self.app.db.conn)
        self.dividends_repo = DividendsRepo(self.app.db.conn)
        self.current_page = 0
        self.ts_from = ts_from
        self.ts_to = ts_to
        self.main_column_id = HistoryTableModel.columns_types[0]
        self.order = Qt.AscendingOrder
        self.transfers_data = []

    def set_period(self, ts_from, ts_to):
        """
        Filter table by given timestamps
        """
        logging.debug("Filtering from {0} to {1}".format(
            datetime.datetime.fromtimestamp(ts_from).isoformat(' '),
            datetime.datetime.fromtimestamp(ts_to).isoformat(' '))
        )
        self.ts_from = ts_from
        self.ts_to = ts_to
        self.init_transfers()

    def set_current_page(self, page):
        self.current_page = page - 1
        self.init_transfers()

    def pages(self):
        return self.sql_adapter.pages(self.app.currency,
                                      self.connection.pubkey,
                                      ts_from=self.ts_from,
                                      ts_to=self.ts_to)

    def pubkeys(self, row):
        return self.transfers_data[row][HistoryTableModel.columns_types.index('pubkey')].split('\n')

    def transfers_and_dividends(self):
        """
        Transfer
        :rtype: List[sakia.data.entities.Transfer]
        """
        return self.sql_adapter.transfers_and_dividends(self.app.currency,
                                                        self.connection.pubkey,
                                                        page=self.current_page,
                                                        ts_from=self.ts_from,
                                                        ts_to=self.ts_to,
                                                        sort_by=HistoryTableModel.columns_to_sql[self.main_column_id],
                                                        sort_order= "ASC" if Qt.AscendingOrder else "DESC")

    def change_transfer(self, transfer):
        for i, data in enumerate(self.transfers_data):
            if data[HistoryTableModel.columns_types.index('txhash')] == transfer.sha_hash:
                if transfer.state == Transaction.DROPPED:
                    self.beginRemoveRows(QModelIndex(), i, i)
                    self.transfers_data.pop(i)
                    self.endRemoveRows()
                else:
                    if self.connection.pubkey in transfer.issuers:
                        self.transfers_data[i] = self.data_sent(transfer)
                        self.dataChanged.emit(self.index(i, 0), self.index(i, len(HistoryTableModel.columns_types)))
                    if self.connection.pubkey in transfer.receivers:
                        self.transfers_data[i] = self.data_received(transfer)
                        self.dataChanged.emit(self.index(i, 0), self.index(i, len(HistoryTableModel.columns_types)))

    def data_received(self, transfer):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Transaction transfer: the transaction
        :return: data as tuple
        """
        block_number = transfer.written_block

        amount = transfer.amount * 10**transfer.amount_base

        senders = []
        for issuer in transfer.issuers:
            identity = self.identities_service.get_identity(issuer)
            if identity:
                senders.append(issuer + " (" + identity.uid + ")")
            else:
                senders.append(issuer)

        date_ts = transfer.timestamp
        txid = transfer.txid

        return (date_ts, "\n".join(senders), amount,
                transfer.comment, transfer.state, txid,
                transfer.issuers, block_number, transfer.sha_hash, transfer)

    def data_sent(self, transfer):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Transaction transfer: the transaction
        :return: data as tuple
        """
        block_number = transfer.written_block

        amount = transfer.amount * 10**transfer.amount_base * -1
        receivers = []
        for receiver in transfer.receivers:
            identity = self.identities_service.get_identity(receiver)
            if identity:
                receivers.append(receiver + " (" + identity.uid + ")")
            else:
                receivers.append(receiver)

        date_ts = transfer.timestamp
        txid = transfer.txid
        return (date_ts, "\n".join(receivers), amount, transfer.comment, transfer.state, txid,
                transfer.receivers, block_number, transfer.sha_hash, transfer)

    def data_dividend(self, dividend):
        """
        Converts a transaction to table data
        :param sakia.data.entities.Dividend dividend: the dividend
        :return: data as tuple
        """
        block_number = dividend.block_number

        amount = dividend.amount * 10**dividend.base
        identity = self.identities_service.get_identity(dividend.pubkey)
        if identity:
            receiver = dividend.pubkey + " (" + identity.uid + ")"
        else:
            receiver = dividend.pubkey

        date_ts = dividend.timestamp
        return (date_ts, receiver, amount, "", HistoryTableModel.DIVIDEND, 0,
                dividend.pubkey, block_number, "", dividend)

    def init_transfers(self):
        self.beginResetModel()
        self.transfers_data = []
        transfers_and_dividends = self.transfers_and_dividends()
        for data in transfers_and_dividends:
            if data[4]: # If data is transfer, it has a sha_hash column
                transfer = self.transactions_repo.get_one(currency=self.app.currency,
                                                          pubkey=self.connection.pubkey,
                                                          sha_hash=data[4])

                if transfer.state != Transaction.DROPPED:
                    if data[2] < 0:
                        self.transfers_data.append(self.data_sent(transfer))
                    else:
                        self.transfers_data.append(self.data_received(transfer))
            else:
                # else we get the dividend depending on the block number
                dividend = self.dividends_repo.get_one(currency=self.app.currency,
                                                       pubkey=self.connection.pubkey,
                                                       block_number=data[5])
                self.transfers_data.append(self.data_dividend(dividend))
        self.endResetModel()

    def rowCount(self, parent):
        return len(self.transfers_data)

    def columnCount(self, parent):
        return len(HistoryTableModel.columns_types) - 6

    def sort(self, main_column, order):
        self.main_column_id = self.columns_types[main_column]
        self.order = order
        self.init_transfers()

    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if HistoryTableModel.columns_types[section] == 'amount':
                dividend, base = self.blockchain_processor.last_ud(self.app.currency)
                header = '{:}'.format(HistoryTableModel.columns_headers[section])
                if self.app.current_ref.base_str(base):
                    header += " ({:})".format(self.app.current_ref.base_str(base))
                return header
            return HistoryTableModel.columns_headers[section]

    def data(self, index, role):
        row = index.row()
        col = index.column()

        if not index.isValid():
            return QVariant()

        source_data = self.transfers_data[row][col]
        state_data = self.transfers_data[row][HistoryTableModel.columns_types.index('state')]
        block_data = self.transfers_data[row][HistoryTableModel.columns_types.index('block_number')]

        if state_data == Transaction.VALIDATED and block_data:
            current_confirmations = self.blockchain_processor.current_buid(self.app.currency).number - block_data
        else:
            current_confirmations = 0

        if role == Qt.DisplayRole:
            if col == HistoryTableModel.columns_types.index('pubkey'):
                return "<p>" + source_data.replace('\n', "<br>") + "</p>"
            if col == HistoryTableModel.columns_types.index('date'):
                ts = self.blockchain_processor.adjusted_ts(self.connection.currency, source_data)
                return QLocale.toString(
                    QLocale(),
                    QDateTime.fromTime_t(ts).date(),
                    QLocale.dateFormat(QLocale(), QLocale.ShortFormat)
                ) + " BAT"
            if col == HistoryTableModel.columns_types.index('amount'):
                amount = self.app.current_ref.instance(source_data, self.connection.currency,
                                                       self.app, block_data).diff_localized(False, False)
                return amount
            return source_data

        if role == Qt.FontRole:
            font = QFont()
            if state_data == Transaction.AWAITING or \
                    (state_data == Transaction.VALIDATED and current_confirmations < MAX_CONFIRMATIONS):
                font.setItalic(True)
            elif state_data == Transaction.REFUSED:
                font.setItalic(True)
            elif state_data == Transaction.TO_SEND:
                font.setBold(True)
            else:
                font.setItalic(False)
            return font

        if role == Qt.ForegroundRole:
            color = None
            if state_data == Transaction.REFUSED:
                color = QColor(Qt.darkGray)
            elif state_data == Transaction.TO_SEND:
                color = QColor(Qt.blue)
            if col == HistoryTableModel.columns_types.index('amount'):
                if source_data < 0:
                    color = QColor(Qt.darkRed)
                elif state_data == HistoryTableModel.DIVIDEND:
                    color = QColor(Qt.darkBlue)
            if state_data == Transaction.AWAITING or \
                    (state_data == Transaction.VALIDATED and current_confirmations == 0):
                color = QColor("#ffb000")
            if color:
                if self.app.parameters.dark_theme:
                    return color.lighter(300)
                else:
                    return color

        if role == Qt.TextAlignmentRole:
            if HistoryTableModel.columns_types.index('amount'):
                return Qt.AlignRight | Qt.AlignVCenter
            if col == HistoryTableModel.columns_types.index('date'):
                return Qt.AlignCenter

        if role == Qt.ToolTipRole:
            if col == HistoryTableModel.columns_types.index('date'):
                ts = self.blockchain_processor.adjusted_ts(self.connection.currency, source_data)
                return QDateTime.fromTime_t(ts).toString(Qt.SystemLocaleLongDate)

            if state_data == Transaction.VALIDATED or state_data == Transaction.AWAITING:
                if current_confirmations >= MAX_CONFIRMATIONS:
                    return None
                elif self.app.parameters.expert_mode:
                    return self.tr("{0} / {1} confirmations").format(current_confirmations, MAX_CONFIRMATIONS)
                else:
                    confirmation = current_confirmations / MAX_CONFIRMATIONS * 100
                    confirmation = 100 if confirmation > 100 else confirmation
                    return self.tr("Confirming... {0} %").format(QLocale().toString(float(confirmation), 'f', 0))

    def flags(self, index):
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled

