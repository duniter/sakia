from PyQt5.QtCore import QObject
from duniterpy.api import bma
import asyncio


class BlockchainService(QObject):
    """
    Blockchain service is managing new blocks received
    to update data locally
    """
    def __init__(self, currency, blockchain_processor, bma_connector, identities_service):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.BlockchainProcessor blockchain_processor: the blockchain processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        :param sakia.services.IdentitiesService identities_service: The identities service
        """
        super().__init__()
        self._blockchain_processor = blockchain_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._identities_service = identities_service

    async def handle_blockchain_progress(self, new_block_uid):
        """
        Handle a new current block uid
        :param duniterpy.documents.BlockUID new_block_uid: the new current blockuid
        """
        local_current_buid = self._blockchain_processor.current_buid()
        with_identities = await self._blockchain_processor.new_blocks_with_identities()
        with_money = await self._blockchain_processor.new_blocks_with_money()
        blocks = await self._blockchain_processor.blocks(with_identities + with_money)
        self._identities_service.handle_new_blocks(blocks)

