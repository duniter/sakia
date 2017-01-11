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
    def __init__(self, app, currency, blockchain_processor, bma_connector, identities_service, transactions_service):
        """
        Constructor the identities service

        :param sakia.app.Application app: Sakia application
        :param str currency: The currency name of the community
        :param sakia.data.processors.BlockchainProcessor blockchain_processor: the blockchain processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        :param sakia.services.IdentitiesService identities_service: The identities service
        :param sakia.services.TransactionsService transactions_service: The transactions service
        """
        super().__init__()
        self.app = app
        self._blockchain_processor = blockchain_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._identities_service = identities_service
        self._transactions_service = transactions_service
        self._logger = logging.getLogger('sakia')

    async def handle_blockchain_progress(self, network_blockstamp):
        """
        Handle a new current block uid

        :param duniterpy.documents.BlockUID network_blockstamp:
        """
        try:
            with_identities = await self._blockchain_processor.new_blocks_with_identities(self.currency)
            with_money = await self._blockchain_processor.new_blocks_with_money(self.currency)
            blocks = await self._blockchain_processor.blocks(with_identities + with_money + [network_blockstamp.number],
                                                             self.currency)
            if len(blocks) > 0:
                identities = await self._identities_service.handle_new_blocks(blocks)
                changed_tx, new_tx, new_dividends = await self._transactions_service.handle_new_blocks(blocks)
                self._blockchain_processor.handle_new_blocks(self.currency, blocks)
                self.app.db.commit()
                for tx in changed_tx:
                    self.app.transaction_state_changed.emit(tx)
                for tx in new_tx:
                    self.app.new_transfer.emit(tx)
                for ud in new_dividends:
                    self.app.new_dividend.emit(ud)
                for idty in identities:
                    self.app.identity_changed.emit(idty)
        except (NoPeerAvailable, DuniterError) as e:
            self._logger.debug(str(e))

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

    def computed_dividend(self):
        """
        Computes next dividend value
        :rtype: int
        """
        parameters = self.parameters()
        next_ud = parameters.c * self.current_mass() / self.last_members_count()
        return math.ceil(next_ud)
