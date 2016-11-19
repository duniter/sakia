from PyQt5.QtCore import QObject
from duniterpy.api import bma
from duniterpy.grammars.output import Condition
from duniterpy.documents.transaction import reduce_base
from duniterpy.documents import Transaction, SimpleTransaction
from duniterpy.api import errors
from sakia.data.entities import Transaction
import math
import logging
import hashlib


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
        :param sakia.data.processors.TransactionProcessor transactions_processor: the transactions processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._transactions_processor = transactions_processor
        self._identities_processor = identities_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    async def _parse_transaction(self, tx_doc, blockUID, mediantime, txid):
        """
        Parse a transaction
        :param sakia.core.Community community: The community
        :param duniterpy.documents.Transaction tx_doc: The tx json data
        :param duniterpy.documents.BlockUID blockUID: The block id where we found the tx
        :param int mediantime: Median time on the network
        :param int txid: The latest txid
        :return: the found transaction
        """
        receivers = [o.conditions.left.pubkey for o in tx_doc.outputs
                     if o.conditions.left.pubkey != tx_doc.issuers[0]]

        if len(receivers) == 0:
            receivers = [tx_doc.issuers[0]]

        in_issuers = len([i for i in tx_doc.issuers
                     if i == self.wallet.pubkey]) > 0
        in_outputs = len([o for o in tx_doc.outputs
                       if o.conditions.left.pubkey == self.wallet.pubkey]) > 0

        tx_hash = hashlib.sha256(tx_doc.signed_raw().encode("ascii")).hexdigest().upper()
        if in_issuers or in_outputs:
            # If the wallet pubkey is in the issuers we sent this transaction
            if in_issuers:
                outputs = [o for o in tx_doc.outputs
                           if o.conditions.left.pubkey != self.wallet.pubkey]
                amount = 0
                for o in outputs:
                    amount += o.amount * math.pow(10, o.base)
            # If we are not in the issuers,
            # maybe we are in the recipients of this transaction
            else:
                outputs = [o for o in tx_doc.outputs
                           if o.conditions.left.pubkey == self.wallet.pubkey]
            amount = 0
            for o in outputs:
                amount += o.amount * math.pow(10, o.base)
            amount, amount_base = reduce_base(amount, 0)

            transaction = Transaction(currency=self.currency,
                                      sha_hash=tx_hash,
                                      written_on=blockUID.number,
                                      blockstamp=tx_doc.blockstamp,
                                      timestamp=mediantime,
                                      signature=tx_doc.signatures[0],
                                      issuer=tx_doc.issuers[0],
                                      receiver=receivers[0],
                                      amount=amount,
                                      amount_base=amount_base,
                                      comment=tx_doc.comment,
                                      txid=txid)
            return transaction
        return None

    async def _parse_block(self, block_doc, txid):
        """
        Parse a block
        :param duniterpy.documents.Block block_doc: The block
        :param int txid: Latest tx id
        :return: The list of transfers sent
        """
        transfers = []
        for tx in [t for t in self._transactions_processor.awaiting()]:
            self._transactions_processor.run_state_transitions(tx, (False, block_doc))

            new_transactions = [t for t in block_doc.transactions
                      if not self._transactions_processor.find_by_hash(t.sha_hash)
                       and SimpleTransaction.is_simple(t)]

            for (i, tx_doc) in enumerate(new_transactions):
                tx = await self._parse_transaction(tx_doc, block_doc.blockUID,
                                        block_doc.mediantime, txid+i)
                if tx:
                    #logging.debug("Transfer amount : {0}".format(transfer.metadata['amount']))
                    transfers.append(tx)
                else:
                    pass
                    #logging.debug("None transfer")
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
