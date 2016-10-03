import attr
import re
from ..entities import Blockchain
from duniterpy.api import bma
from duniterpy.documents import Block
import asyncio


@attr.s
class BlockchainProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.CertificationsRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector

    def current_buid(self, currency):
        """
        Get the local current blockuid
        :rtype: duniterpy.documents.BlockUID
        """
        return self._repo.get_one({'currency': currency}).current_buid

    def time(self, currency):
        """
        Get the local current median time
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).median_time

    def parameters(self, currency):
        """
        Get the parameters of the blockchain
        :rtype: sakia.data.entities.BlockchainParameters
        """
        return self._repo.get_one({'currency': currency}).parameters

    def monetary_mass(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).monetary_mass

    def nb_members(self, currency):
        """
        Get the number of members in the blockchain
        :rtype: int
        """
        return self._repo.get_one({'currency': currency}).nb_members

    def last_ud(self, currency):
        """
        Get the last ud value and base
        :rtype: int, int
        """
        blockchain = self._repo.get_one({'currency': currency})
        return blockchain.last_ud, blockchain.last_ud_base

    async def new_blocks_with_identities(self, currency):
        """
        Get blocks more recent than local blockuid
        with identities
        """
        with_identities = []
        future_requests = []
        for req in (bma.blockchain.Joiners,
                    bma.blockchain.Leavers,
                    bma.blockchain.Actives,
                    bma.blockchain.Excluded,
                    bma.blockchain.Newcomers):
            future_requests.append(self._bma_connector.get(req))
        results = await asyncio.gather(future_requests)

        for res in results:
            with_identities += res["result"]["blocks"]

        local_current_buid = self.current_buid()
        return sorted([b for b in with_identities if b > local_current_buid.number])

    async def new_blocks_with_money(self, currency):
        """
        Get blocks more recent than local block uid
        with money data (tx and uds)
        """
        with_money = []
        future_requests = []
        for req in (bma.blockchain.UD, bma.blockchain.TX):
            future_requests.append(self._bma_connector.get(req))
        results = await asyncio.gather(future_requests)

        for res in results:
            with_money += res["result"]["blocks"]

        local_current_buid = self.current_buid()
        return sorted([b for b in with_money if b > local_current_buid.number])

    async def blocks(self, numbers, currency):
        """
        Get blocks from the network
        :param List[int] numbers: list of blocks numbers to get
        :return: the list of block documents
        :rtype: List[duniterpy.documents.Block]
        """
        from_block = min(numbers)
        to_block = max(numbers)
        count = to_block - from_block

        blocks_data = await self._bma_connector.get(bma.blockchain.Blocks, req_args={'count': count,
                                                                                     'from_': from_block})
        blocks = []
        for data in blocks_data:
            if data['number'] in numbers:
                blocks.append(Block.from_signed_raw(data["raw"] + data["signature"] + "\n"))

        return blocks

