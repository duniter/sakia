from PyQt5.QtCore import QObject
from sakia.data.entities.transaction import parse_transaction_doc
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents import SimpleTransaction
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

    def _parse_block(self, block_doc, txid):
        """
        Parse a block
        :param duniterpy.documents.Block block_doc: The block
        :param int txid: Latest tx id
        :return: The list of transfers sent
        """
        transfers_changed = []
        new_transfers = []
        for tx in [t for t in self._transactions_processor.awaiting(self.currency)]:
            if self._transactions_processor.run_state_transitions(tx, block_doc):
                transfers_changed.append(tx)
                self._logger.debug("New transaction validated : {0}".format(tx.sha_hash))

        new_transactions = [t for t in block_doc.transactions
                            if not self._transactions_processor.find_by_hash(t.sha_hash)
                            and SimpleTransaction.is_simple(t)]
        connections_pubkeys = [c.pubkey for c in self._connections_processor.connections_to(self.currency)]
        for pubkey in connections_pubkeys:
            for (i, tx_doc) in enumerate(new_transactions):
                tx = parse_transaction_doc(tx_doc, pubkey, block_doc.blockUID.number,  block_doc.mediantime, txid+i)
                if tx:
                    new_transfers.append(tx)
                    self._transactions_processor.commit(tx)
                else:
                    logging.debug("Error during transfer parsing")

        return transfers_changed, new_transfers

    async def handle_new_blocks(self, blocks):
        """
        Refresh last transactions

        :param list[duniterpy.documents.Block] blocks: The blocks containing data to parse
        """
        self._logger.debug("Refresh transactions")
        transfers_changed = []
        new_transfers = []
        txid = 0
        for block in blocks:
            changes, new_tx = self._parse_block(block, txid)
            txid += len(new_tx)
            transfers_changed += changes
            new_transfers += new_tx
        new_dividends = await self.parse_dividends_history(blocks, new_transfers)
        return transfers_changed, new_transfers, new_dividends

    async def parse_dividends_history(self, blocks, transactions):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param List[duniterpy.documents.Block] blocks: the list of transactions found by tx parsing
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx parsing
        """
        connections_pubkeys = [c.pubkey for c in self._connections_processor.connections_to(self.currency)]
        min_block_number = blocks[0].number
        dividends = []
        for pubkey in connections_pubkeys:
            history_data = await self._bma_connector.get(self.currency, bma.ud.history,
                                                         req_args={'pubkey': pubkey})
            block_numbers = []
            for ud_data in history_data["history"]["history"]:
                dividend = Dividend(currency=self.currency,
                                    pubkey=pubkey,
                                    block_number=ud_data["block_number"],
                                    timestamp=ud_data["time"],
                                    amount=ud_data["amount"],
                                    base=ud_data["base"])
                if dividend.block_number > min_block_number:
                    self._logger.debug("Dividend of block {0}".format(dividend.block_number))
                    block_numbers.append(dividend.block_number)
                    if self._dividends_processor.commit(dividend):
                        dividends.append(dividend)

            for tx in transactions:
                txdoc = TransactionDoc.from_signed_raw(tx.raw)
                for input in txdoc.inputs:
                    if input.source == "D" and input.origin_id == pubkey and input.index not in block_numbers:
                        block = next((b for b in blocks if b.number == input.index))
                        dividend = Dividend(currency=self.currency,
                                            pubkey=pubkey,
                                            block_number=input.index,
                                            timestamp=block.mediantime,
                                            amount=block.ud,
                                            base=block.unit_base)
                        self._logger.debug("Dividend of block {0}".format(dividend.block_number))
                        if self._dividends_processor.commit(dividend):
                            dividends.append(dividend)
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