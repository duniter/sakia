from PyQt5.QtCore import QObject
from sakia.data.entities.transaction import parse_transaction_doc, Transaction, build_stopline
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents import SimpleTransaction, Block
from sakia.data.entities import Dividend
from duniterpy.api import bma
import logging
import sqlite3


class TransactionsService(QObject):
    """
    Transaction service is managing sources received
    to update data locally
    """
    def __init__(self, currency, transactions_processor, dividends_processor,
                 identities_processor, connections_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor for given currency
        :param sakia.data.processors.TransactionsProcessor transactions_processor: the transactions processor for given currency
        :param sakia.data.processors.DividendsProcessor dividends_processor: the dividends processor for given currency
        :param sakia.data.processors.ConnectionsProcessor connections_processor: the connections processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._transactions_processor = transactions_processor
        self._dividends_processor = dividends_processor
        self._identities_processor = identities_processor
        self._connections_processor = connections_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    def parse_sent_transaction(self, pubkey, transaction):
        """
        Parse a block
        :param sakia.data.entities.Transaction transaction: The transaction to parse
        :return: The list of transfers sent
        """
        if not self._transactions_processor.find_by_hash(pubkey, transaction.sha_hash):
            txid = self._transactions_processor.next_txid(transaction.currency, -1)
            tx = parse_transaction_doc(transaction.txdoc(), pubkey,
                                       transaction.blockstamp.number,  transaction.timestamp, txid+1)
            if tx:
                tx.state = Transaction.AWAITING
                self._transactions_processor.commit(tx)
                return tx
            else:
                logging.debug("Error during transfer parsing")

    def insert_stopline(self, connections, block_number, time):
        for conn in connections:
            self._transactions_processor.commit(build_stopline(conn.currency, conn.pubkey, block_number, time))

    async def handle_new_blocks(self, connections, start, end):
        """
        Refresh last transactions

        :param list[duniterpy.documents.Block] blocks: The blocks containing data to parse
        """
        self._logger.debug("Refresh transactions")
        transfers_changed, new_transfers = await self.parse_transactions_history(connections, start, end)
        new_dividends = await self.parse_dividends_history(connections, start, end, new_transfers)
        return transfers_changed, new_transfers, new_dividends

    async def parse_transactions_history(self, connections, start, end):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param List[sakia.data.entities.Connection] connections: the list of connections found by tx parsing
        :param int start: the first block
        :param int end: the last block
        """
        transfers_changed = []
        new_transfers = {}
        for connection in connections:
            txid = 0
            new_transfers[connection] = []
            history_data = await self._bma_connector.get(self.currency, bma.tx.blocks,
                                                         req_args={'pubkey': connection.pubkey,
                                                                   'start': start,
                                                                   'end': end})
            for tx_data in history_data["history"]["sent"]:
                for tx in [t for t in self._transactions_processor.awaiting(self.currency)]:
                    if self._transactions_processor.run_state_transitions(tx, tx_data["hash"], tx_data["block_number"]):
                        transfers_changed.append(tx)
                        self._logger.debug("New transaction validated : {0}".format(tx.sha_hash))
            for tx_data in history_data["history"]["received"]:
                tx_doc = TransactionDoc.from_bma_history(history_data["currency"], tx_data)
                if not self._transactions_processor.find_by_hash(connection.pubkey, tx_doc.sha_hash) \
                    and SimpleTransaction.is_simple(tx_doc):
                    tx = parse_transaction_doc(tx_doc, connection.pubkey, tx_data["block_number"],
                                               tx_data["time"], txid)
                    if tx:
                        new_transfers[connection].append(tx)
                        self._transactions_processor.commit(tx)
                    else:
                        logging.debug("Error during transfer parsing")
        return transfers_changed, new_transfers

    async def parse_dividends_history(self, connections, start, end, transactions):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param List[sakia.data.entities.Connection] connections: the list of connections found by tx parsing
        :param List[duniterpy.documents.Block] blocks: the list of transactions found by tx parsing
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx parsing
        """
        dividends = {}
        for connection in connections:
            dividends[connection] = []
            history_data = await self._bma_connector.get(self.currency, bma.ud.history,
                                                         req_args={'pubkey': connection.pubkey})
            block_numbers = []
            for ud_data in history_data["history"]["history"]:
                dividend = Dividend(currency=self.currency,
                                    pubkey=connection.pubkey,
                                    block_number=ud_data["block_number"],
                                    timestamp=ud_data["time"],
                                    amount=ud_data["amount"],
                                    base=ud_data["base"])
                if start <= dividend.block_number <= end:
                    self._logger.debug("Dividend of block {0}".format(dividend.block_number))
                    block_numbers.append(dividend.block_number)
                    if self._dividends_processor.commit(dividend):
                        dividends[connection].append(dividend)

            for tx in transactions[connection]:
                txdoc = TransactionDoc.from_signed_raw(tx.raw)
                for input in txdoc.inputs:
                    # For each dividends inputs, if it is consumed (not present in ud history)
                    if input.source == "D" and input.origin_id == connection.pubkey and input.index not in block_numbers:
                        block_data = await self._bma_connector.get(self.currency, bma.blockchain.block,
                                                              req_args={'number': input.index})
                        block = Block.from_signed_raw(block_data["raw"] + block_data["signature"] + "\n")
                        dividend = Dividend(currency=self.currency,
                                            pubkey=connection.pubkey,
                                            block_number=input.index,
                                            timestamp=block.mediantime,
                                            amount=block.ud,
                                            base=block.unit_base)
                        self._logger.debug("Dividend of block {0}".format(dividend.block_number))
                        if self._dividends_processor.commit(dividend):
                            dividends[connection].append(dividend)
        return dividends

    def transfers(self, pubkey):
        """
        Get all transfers from or to a given pubkey
        :param str pubkey:
        :return: the list of Transaction entities
        :rtype: List[sakia.data.entities.Transaction]
        """
        return self._transactions_processor.transfers(self.currency, pubkey)

    def dividends(self, pubkey):
        """
        Get all dividends from or to a given pubkey
        :param str pubkey:
        :return: the list of Dividend entities
        :rtype: List[sakia.data.entities.Dividend]
        """
        return self._dividends_processor.dividends(self.currency, pubkey)