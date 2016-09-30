import attr
import re
from ..entities import Blockchain
from duniterpy.api import bma
from duniterpy.documents import Block
import asyncio


@attr.s
class BlockchainProcessor:
    _currency = attr.ib()  # :type str
    _repo = attr.ib()  # :type sakia.data.repositories.CertificationsRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector

    def current_buid(self):
        """
        Get the local current blockuid
        :rtype: duniterpy.documents.BlockUID
        """
        return self._repo.get_one({'currency': self._currency}).current_buid

    def time(self):
        """
        Get the local current median time
        :rtype: int
        """
        return self._repo.get_one({'currency': self._currency}).median_time

    def parameters(self):
        """
        Get the parameters of the blockchain
        :rtype: sakia.data.entities.BlockchainParameters
        """
        return self._repo.get_one({'currency': self._currency}).parameters

    def monetary_mass(self):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one({'currency': self._currency}).monetary_mass

    def nb_members(self):
        """
        Get the number of members in the blockchain
        :rtype: int
        """
        return self._repo.get_one({'currency': self._currency}).nb_members

    def last_ud(self):
        """
        Get the last ud value and base
        :rtype: int, int
        """
        blockchain = self._repo.get_one({'currency': self._currency})
        return blockchain.last_ud, blockchain.last_ud_base

    @property
    def short_currency(self):
        """
        Format the currency name to a short one

        :return: The currency name in a shot format.
        """
        words = re.split('[_\W]+', self.currency)
        shortened = ""
        if len(words) > 1:
            shortened = ''.join([w[0] for w in words])
        else:
            vowels = ('a', 'e', 'i', 'o', 'u', 'y')
            shortened = self.currency
            shortened = ''.join([c for c in shortened if c not in vowels])
        return shortened.upper()

    @property
    def currency_symbol(self):
        """
        Format the currency name to a symbol one.

        :return: The currency name as a utf-8 circled symbol.
        """
        letter = self.currency[0]
        u = ord('\u24B6') + ord(letter) - ord('A')
        return chr(u)

    async def new_blocks_with_identities(self):
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

    async def new_blocks_with_money(self):
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

    async def blocks(self, numbers):
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

