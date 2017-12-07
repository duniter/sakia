from PyQt5.QtCore import QObject
from duniterpy.api import bma, errors
from duniterpy.documents import Transaction as TransactionDoc
from duniterpy.documents import BlockUID
import logging
from sakia.data.entities import Source, Transaction,Dividend
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

    def parse_transaction_outputs(self, pubkey, transaction):
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

    def parse_transaction_inputs(self, pubkey, transaction):
        """
        Parse a transaction
        :param sakia.data.entities.Transaction transaction:
        """
        txdoc = TransactionDoc.from_signed_raw(transaction.raw)
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
                                          pubkey=pubkey,
                                          sha_hash=sha_identifier,
                                          written_block=block_number,
                                          blockstamp=BlockUID.empty(),
                                          timestamp=timestamp,
                                          signatures=[],
                                          issuers=[pubkey],
                                          receivers=[],
                                          amount=amount,
                                          amount_base=0,
                                          comment="Too low balance",
                                          txid=next_txid,
                                          state=Transaction.VALIDATED,
                                          local=True,
                                          raw="")
                self._transactions_processor.commit(destruction)
                return destruction

    async def refresh_sources_of_pubkey(self, pubkey, transactions, dividends, unit_base, log_stream=None,
                                        progress=None):
        """
        Refresh the sources for a given pubkey
        :param str pubkey:
        :param list[sakia.data.entities.Transaction] transactions:
        :param list[sakia.data.entities.Dividend] dividends:
        :param int unit_base: the unit base of the destruction. None to look for the past uds
        :return: the destruction of sources
        """
        tx_ud_data = {}
        for tx in transactions:
            try:
                tx_ud_data[tx.written_block].append(tx)
            except:
                tx_ud_data[tx.written_block] = [tx]
        for ud in dividends:
            try:
                tx_ud_data[ud.block_number].append(ud)
            except:
                tx_ud_data[ud.block_number] = [ud]

        blocks = sorted(b for b in tx_ud_data.keys())

        nb_tx_ud = len(transactions) + len(dividends)
        udblocks = await self._bma_connector.get(self.currency, bma.blockchain.ud)
        destructions = []
        for block_number in blocks:
            if log_stream:
                log_stream("Parsing info ud/tx of {:}".format(block_number))
            if progress:
                progress(1/nb_tx_ud)

            for data in tx_ud_data[block_number]:
                if isinstance(data, Dividend):
                    self._parse_ud(pubkey, data)
                if isinstance(data, Transaction):
                    self.parse_transaction_outputs(pubkey, data)

            for data in tx_ud_data[block_number]:
                if isinstance(data, Transaction):
                    self.parse_transaction_inputs(pubkey, data)

            if not unit_base:
                _, destruction_base = await self._blockchain_processor.ud_before(self.currency, block_number, udblocks)
            else:
                destruction_base = unit_base
            destruction = await self.check_destruction(pubkey, block_number, destruction_base)
            if destruction:
                destructions.append(destruction)
        return destructions

    async def refresh_sources(self, connections, transactions, dividends):
        """

        :param list[sakia.data.entities.Connection] connections:
        :param dict[sakia.data.entities.Transaction] transactions:
        :param dict[sakia.data.entities.Dividend] dividends:
        :return: the destruction of sources
        """
        destructions = {}
        for conn in connections:
            destructions[conn] = []
            _, current_base = self._blockchain_processor.last_ud(self.currency)
            # there can be bugs if the current base switch during the parsing of blocks
            # but since it only happens every 23 years and that its only on accounts having less than 100
            # this is acceptable I guess
            destructions[conn] += await self.refresh_sources_of_pubkey(conn.pubkey, transactions[conn],
                                                                       dividends[conn], current_base)

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
