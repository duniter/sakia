from PyQt5.QtCore import QObject
from duniterpy.api import bma, errors
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents import BlockUID
import logging
from sakia.data.entities import Source, Transaction
import hashlib


class SourcesServices(QObject):
    """
    Source service is managing sources received
    to update data locally
    """
    def __init__(self, currency, sources_processor, connections_processor,
                 transactions_processor, blockchain_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.SourcesProcessor sources_processor: the sources processor for given currency
        :param sakia.data.processors.ConnectionsProcessor connections_processor: the connections processor
        :param sakia.data.processors.TransactionsProcessor transactions_processor: the transactions processor
        :param sakia.data.processors.BlockchainProcessor blockchain_processor: the blockchain processor
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._sources_processor = sources_processor
        self._connections_processor = connections_processor
        self._transactions_processor = transactions_processor
        self._blockchain_processor = blockchain_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    def amount(self, pubkey):
        return self._sources_processor.amount(self.currency, pubkey)

    def parse_transaction(self, pubkey, transaction):
        """
        Parse a transaction
        :param sakia.data.entities.Transaction transaction:
        """
        txdoc = TransactionDoc.from_signed_raw(transaction.raw)
        for offset, output in enumerate(txdoc.outputs):
            if output.conditions.left.pubkey == pubkey:
                source = Source(currency=self.currency,
                                pubkey=pubkey,
                                identifier=txdoc.sha_hash,
                                type='T',
                                noffset=offset,
                                amount=output.amount,
                                base=output.base)
                self._sources_processor.insert(source)
        for index, input in enumerate(txdoc.inputs):
            source = Source(currency=self.currency,
                            pubkey=txdoc.issuers[0],
                            identifier=input.origin_id,
                            type=input.source,
                            noffset=input.index,
                            amount=input.amount,
                            base=input.base)
            if source.pubkey == pubkey:
                self._sources_processor.drop(source)

    def _parse_ud(self, pubkey, dividend):
        """
        :param str pubkey:
        :param sakia.data.entities.Dividend dividend:
        :return:
        """
        source = Source(currency=self.currency,
                        pubkey=pubkey,
                        identifier=pubkey,
                        type='D',
                        noffset=dividend.block_number,
                        amount=dividend.amount,
                        base=dividend.base)
        self._sources_processor.insert(source)

    async def check_destruction(self, pubkey, block_number, unit_base):
        amount = self._sources_processor.amount(self.currency, pubkey)
        if amount < 100 * 10 ** unit_base:
            if self._sources_processor.available(self.currency, pubkey):
                self._sources_processor.drop_all_of(self.currency, pubkey)
                timestamp = await self._blockchain_processor.timestamp(self.currency, block_number)
                next_txid = self._transactions_processor.next_txid(self.currency, block_number)
                sha_identifier = hashlib.sha256("Destruction{0}{1}{2}".format(block_number, pubkey, amount).encode("ascii")).hexdigest().upper()
                destruction = Transaction(currency=self.currency,
                                          sha_hash=sha_identifier,
                                          written_block=block_number,
                                          blockstamp=BlockUID.empty(),
                                          timestamp=timestamp,
                                          signature="",
                                          issuer=pubkey,
                                          receivers="",
                                          amount=amount,
                                          amount_base=0,
                                          comment="Too low balance",
                                          txid=next_txid,
                                          state=Transaction.VALIDATED,
                                          local=True,
                                          raw="")
                self._transactions_processor.commit(destruction)
                return destruction

    async def refresh_sources_of_pubkey(self, pubkey, transactions, dividends, unit_base):
        """
        Refresh the sources for a given pubkey
        :param str pubkey:
        :param list[sakia.data.entities.Transaction] transactions:
        :param list[sakia.data.entities.Dividend] dividends:
        :param int unit_base: the unit base of the destruction. None to look for the past uds
        :return: the destruction of sources
        """
        sorted_tx = (s for s in sorted(transactions, key=lambda t: t.written_block))
        sorted_ud = (u for u in sorted(dividends, key=lambda d: d.block_number))
        try:
            tx = next(sorted_tx)
            block_number = max(tx.written_block, 0)
        except StopIteration:
            tx = None
            block_number = 0
        try:
            ud = next(sorted_ud)
            block_number = min(block_number, ud.block_number)
        except StopIteration:
            ud = None

        destructions = []
        while tx or ud:
            if tx and tx.written_block == block_number:
                self.parse_transaction(pubkey, tx)
                try:
                    tx = next(sorted_tx)
                except StopIteration:
                    tx = None
            if ud and ud.block_number == block_number:
                self._parse_ud(pubkey, ud)
                try:
                    ud = next(sorted_ud)
                except StopIteration:
                    ud = None
            if not unit_base:
                _, destruction_base = await self._blockchain_processor.ud_before(self.currency, block_number)
            else:
                destruction_base = unit_base
            destruction = await self.check_destruction(pubkey, block_number, destruction_base)
            if destruction:
                destructions.append(destruction)
            if ud and tx:
                block_number = min(ud.block_number, tx.written_block)
            elif ud:
                block_number = ud.block_number
            elif tx:
                block_number = tx.written_block
        return destructions

    async def refresh_sources(self, transactions, dividends):
        """

        :param list[sakia.data.entities.Transaction] transactions:
        :param list[sakia.data.entities.Dividend] dividends:
        :return: the destruction of sources
        """
        connections_pubkeys = [c.pubkey for c in self._connections_processor.connections_to(self.currency)]
        destructions = []
        for pubkey in connections_pubkeys:
            _, current_base = self._blockchain_processor.last_ud(self.currency)
            # there can be bugs if the current base switch during the parsing of blocks
            # but since it only happens every 23 years and that its only on accounts having less than 100
            # this is acceptable I guess
            destructions += await self.refresh_sources_of_pubkey(pubkey, transactions, dividends, current_base)
        return destructions

    def restore_sources(self, pubkey, tx):
        """
        Restore the sources of a cancelled tx
        :param sakia.entities.Transaction tx:
        """
        txdoc = TransactionDoc.from_signed_raw(tx.raw)
        for offset, output in enumerate(txdoc.outputs):
            if output.conditions.left.pubkey == pubkey:
                source = Source(currency=self.currency,
                                pubkey=pubkey,
                                identifier=txdoc.sha_hash,
                                type='T',
                                noffset=offset,
                                amount=output.amount,
                                base=output.base)
                self._sources_processor.drop(source)
        for index, input in enumerate(txdoc.inputs):
            source = Source(currency=self.currency,
                            pubkey=txdoc.issuers[0],
                            identifier=input.origin_id,
                            type=input.source,
                            noffset=input.index,
                            amount=input.amount,
                            base=input.base)
            if source.pubkey == pubkey:
                self._sources_processor.insert(source)
