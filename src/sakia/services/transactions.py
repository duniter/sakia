from PyQt5.QtCore import QObject
from sakia.data.entities.transaction import parse_transaction_doc
from duniterpy.documents import SimpleTransaction
import logging


class TransactionsService(QObject):
    """
    Transaction service is managing sources received
    to update data locally
    """
    def __init__(self, currency, transactions_processor, identities_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor for given currency
        :param sakia.data.processors.TransactionsProcessor transactions_processor: the transactions processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._transactions_processor = transactions_processor
        self._identities_processor = identities_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    async def _parse_block(self, block_doc, txid):
        """
        Parse a block
        :param duniterpy.documents.Block block_doc: The block
        :param int txid: Latest tx id
        :return: The list of transfers sent
        """
        transfers = []
        for tx in [t for t in self._transactions_processor.awaiting(self.currency)]:
            self._transactions_processor.run_state_transitions(tx, (False, block_doc))

            new_transactions = [t for t in block_doc.transactions
                      if not self._transactions_processor.find_by_hash(t.sha_hash)
                       and SimpleTransaction.is_simple(t)]

            for (i, tx_doc) in enumerate(new_transactions):
                tx = parse_transaction_doc(tx_doc, block_doc.blockUID.number,  block_doc.mediantime, txid+i)
                if tx:
                    #logging.debug("Transfer amount : {0}".format(transfer.metadata['amount']))
                    self._transactions_processor.commit(tx)
                else:
                    logging.debug("Error during transfer parsing")
        return transfers

    async def handle_new_blocks(self, blocks):
        """
        Refresh last transactions

        :param list[duniterpy.documents.Block] blocks: The blocks containing data to parse
        """
        self._logger.debug("Refresh transactions")
        txid = 0
        for block in blocks:
            transfers = await self._parse_block(block, txid)
            txid += len(transfers)

    def transfers(self, pubkey):
        """
        Get all transfers from or to a given pubkey
        :param str pubkey:
        :return: the list of Transaction entities
        :rtype: List[sakia.data.entities.Transaction]
        """
        return self._transactions_processor.transfers(self.currency, pubkey)