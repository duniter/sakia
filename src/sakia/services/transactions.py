from PyQt5.QtCore import QObject
from sakia.data.entities.transaction import parse_transaction_doc, Transaction
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

    def _parse_block(self, connections, block_doc, txid):
        """
        Parse a block
        :param duniterpy.documents.Block block_doc: The block
        :param int txid: Latest tx id
        :return: The list of transfers sent
        """
        transfers_changed = []
        new_transfers = {}
        for tx in [t for t in self._transactions_processor.awaiting(self.currency)]:
            if self._transactions_processor.run_state_transitions(tx, block_doc):
                transfers_changed.append(tx)
                self._logger.debug("New transaction validated : {0}".format(tx.sha_hash))
        for conn in connections:
            new_transactions = [t for t in block_doc.transactions
                                if not self._transactions_processor.find_by_hash(conn.pubkey, t.sha_hash)
                                and SimpleTransaction.is_simple(t)]

            new_transfers[conn] = []
            for (i, tx_doc) in enumerate(new_transactions):
                tx = parse_transaction_doc(tx_doc, conn.pubkey, block_doc.blockUID.number,  block_doc.mediantime, txid+i)
                if tx:
                    new_transfers[conn].append(tx)
                    self._transactions_processor.commit(tx)
                else:
                    logging.debug("Error during transfer parsing")

        return transfers_changed, new_transfers

    async def handle_new_blocks(self, connections, blocks):
        """
        Refresh last transactions

        :param list[duniterpy.documents.Block] blocks: The blocks containing data to parse
        """
        self._logger.debug("Refresh transactions")
        transfers_changed = []
        new_transfers = {}
        txid = 0
        for block in blocks:
            changes, new_tx = self._parse_block(connections, block, txid)
            txid += len(new_tx)
            transfers_changed += changes
            for conn in new_tx:
                try:
                    new_transfers[conn] += new_tx[conn]
                except KeyError:
                    new_transfers[conn] = new_tx[conn]
        new_dividends = await self.parse_dividends_history(connections, blocks, new_transfers)
        return transfers_changed, new_transfers, new_dividends

    async def parse_dividends_history(self, connections, blocks, transactions):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param List[sakia.data.entities.Connection] connections: the list of connections found by tx parsing
        :param List[duniterpy.documents.Block] blocks: the list of transactions found by tx parsing
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx parsing
        """
        min_block_number = blocks[0].number
        max_block_number = blocks[-1].number
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
                if max_block_number >= dividend.block_number >= min_block_number:
                    self._logger.debug("Dividend of block {0}".format(dividend.block_number))
                    block_numbers.append(dividend.block_number)
                    if self._dividends_processor.commit(dividend):
                        dividends[connection].append(dividend)

            for tx in transactions[connection]:
                txdoc = TransactionDoc.from_signed_raw(tx.raw)
                for input in txdoc.inputs:
                    # For each dividends inputs, if it is consumed (not present in ud history)
                    if input.source == "D" and input.origin_id == connection.pubkey and input.index not in block_numbers:
                        try:
                            # we try to get the block of the dividend
                            block = next((b for b in blocks if b.number == input.index))
                        except StopIteration:
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