import asyncio
from PyQt5.QtCore import QObject
import math
import logging
from duniterpy.api.errors import DuniterError
from sakia.errors import NoPeerAvailable


class BlockchainService(QObject):
    """
    Blockchain service is managing new blocks received
    to update data locally
    """
    def __init__(self, app, currency, blockchain_processor, connections_processor, bma_connector,
                 identities_service, transactions_service, sources_service):
        """
        Constructor the identities service

        :param sakia.app.Application app: Sakia application
        :param str currency: The currency name of the community
        :param sakia.data.processors.BlockchainProcessor blockchain_processor: the blockchain processor for given currency
        :param sakia.data.processors.ConnectionsProcessor connections_processor: the connections processor
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        :param sakia.services.IdentitiesService identities_service: The identities service
        :param sakia.services.TransactionsService transactions_service: The transactions service
        :param sakia.services.SourcesService sources_service: The sources service
        """
        super().__init__()
        self.app = app
        self._blockchain_processor = blockchain_processor
        self._connections_processor = connections_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._identities_service = identities_service
        self._transactions_service = transactions_service
        self._sources_service = sources_service
        self._logger = logging.getLogger('sakia')
        self._update_lock = False

    def initialized(self):
        return self._blockchain_processor.initialized(self.app.currency)

    def handle_new_blocks(self, blocks):
        self._blockchain_processor.handle_new_blocks(self.currency, blocks)

    async def new_blocks(self, network_blockstamp):
        with_identities = await self._blockchain_processor.new_blocks_with_identities(self.currency)
        with_money = await self._blockchain_processor.new_blocks_with_money(self.currency)
        block_numbers = with_identities + with_money
        if network_blockstamp > self.current_buid():
            block_numbers += [network_blockstamp.number]
        return block_numbers

    async def handle_blockchain_progress(self, network_blockstamp):
        """
        Handle a new current block uid

        :param duniterpy.documents.BlockUID network_blockstamp:
        """
        if self._blockchain_processor.initialized(self.currency) and not self._update_lock:
            try:
                self._update_lock = True
                self.app.refresh_started.emit()
                block_numbers = await self.new_blocks(network_blockstamp)
                while block_numbers:
                    start = self.current_buid().number
                    self._logger.debug("Parsing from {0}".format(start))
                    blocks = await self._blockchain_processor.next_blocks(start, block_numbers, self.currency)
                    if len(blocks) > 0:
                        connections = self._connections_processor.connections_to(self.currency)
                        identities = await self._identities_service.handle_new_blocks(blocks)
                        changed_tx, new_tx, new_dividends = await self._transactions_service.handle_new_blocks(connections,
                                                                                                               blocks)
                        destructions = await self._sources_service.refresh_sources(connections, new_tx, new_dividends)
                        self.handle_new_blocks(blocks)
                        self.app.db.commit()
                        for tx in changed_tx:
                            self.app.transaction_state_changed.emit(tx)
                        for conn in new_tx:
                            for tx in new_tx[conn]:
                                self.app.new_transfer.emit(conn, tx)
                        for conn in destructions:
                            for tx in destructions[conn]:
                                self.app.new_transfer.emit(conn, tx)
                        for conn in new_dividends:
                            for ud in new_dividends[conn]:
                                self.app.new_dividend.emit(conn, ud)
                        for idty in identities:
                            self.app.identity_changed.emit(idty)
                        self.app.new_blocks_handled.emit()
                        block_numbers = await self.new_blocks(network_blockstamp)
                self.app.sources_refreshed.emit()
            except (NoPeerAvailable, DuniterError) as e:
                self._logger.debug(str(e))
            finally:
                self.app.refresh_finished.emit()
                self._update_lock = False

    def current_buid(self):
        return self._blockchain_processor.current_buid(self.currency)

    def parameters(self):
        return self._blockchain_processor.parameters(self.currency)

    def time(self):
        return self._blockchain_processor.time(self.currency)

    def current_members_count(self):
        return self._blockchain_processor.current_members_count(self.currency)

    def current_mass(self):
        return self._blockchain_processor.current_mass(self.currency)

    def last_monetary_mass(self):
        return self._blockchain_processor.last_mass(self.currency)

    def last_ud(self):
        return self._blockchain_processor.last_ud(self.currency)

    def last_members_count(self):
        return self._blockchain_processor.last_members_count(self.currency)

    def last_ud_time(self):
        return self._blockchain_processor.last_ud_time(self.currency)

    def previous_members_count(self):
        return self._blockchain_processor.previous_members_count(self.currency)

    def previous_monetary_mass(self):
        return self._blockchain_processor.previous_monetary_mass(self.currency)

    def previous_ud_time(self):
        return self._blockchain_processor.previous_ud_time(self.currency)

    def previous_ud(self):
        return self._blockchain_processor.previous_ud(self.currency)

    def adjusted_ts(self, time):
        return self._blockchain_processor.adjusted_ts(self.currency, time)
    
    def next_ud_reeval(self):
        parameters = self._blockchain_processor.parameters(self.currency)
        mediantime = self._blockchain_processor.time(self.currency)
        if parameters.ud_reeval_time_0 == 0 or parameters.dt_reeval == 0:
            return 0
        else:
            ud_reeval = parameters.ud_reeval_time_0
            while ud_reeval <= mediantime:
                ud_reeval += parameters.dt_reeval
            return ud_reeval

    def computed_dividend(self):
        """
        Computes next dividend value
        :rtype: int
        """
        parameters = self.parameters()
        if self.last_members_count():
            last_ud = self.last_ud()[0] * 10**self.last_ud()[1]
            next_ud = last_ud + parameters.c * parameters.c * self.previous_monetary_mass() / self.last_members_count()
        else:
            next_ud = parameters.ud0
        return math.ceil(next_ud)
