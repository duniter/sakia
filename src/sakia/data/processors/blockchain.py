import attr
import sqlite3
import logging
from sakia.errors import NoPeerAvailable
from ..entities import Blockchain, BlockchainParameters
from .nodes import NodesProcessor
from ..connectors import BmaConnector
from duniterpy.api import bma, errors
from duniterpy.documents import Block, BMAEndpoint
import asyncio


@attr.s
class BlockchainProcessor:
    _repo = attr.ib()  # :type sakia.data.repositories.CertificationsRepo
    _bma_connector = attr.ib()  # :type sakia.data.connectors.bma.BmaConnector
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        :rtype: sakia.data.processors.BlockchainProcessor
        """
        return cls(app.db.blockchains_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters))

    def initialized(self, currency):
        return self._repo.get_one(currency=currency) is not None

    async def timestamp(self, currency, block_number):
        try:
            block = await self._bma_connector.get(currency, bma.blockchain.block, {'number': block_number})
            if block:
                return block['medianTime']
        except NoPeerAvailable as e:
            self._logger.debug(str(e))
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                self._logger.debug(str(e))
            else:
                raise
        return 0

    def current_buid(self, currency):
        """
        Get the local current blockuid
        :rtype: duniterpy.documents.BlockUID
        """
        blockchain = self._repo.get_one(currency=currency)
        return blockchain.current_buid

    def time(self, currency):
        """
        Get the local current median time
        :rtype: int
        """
        return self._repo.get_one(currency=currency).median_time

    def parameters(self, currency):
        """
        Get the parameters of the blockchain
        :rtype: sakia.data.entities.BlockchainParameters
        """
        return self._repo.get_one(currency=currency).parameters

    def current_mass(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one(currency=currency).current_mass

    def current_members_count(self, currency):
        """
        Get the number of members in the blockchain
        :rtype: int
        """
        return self._repo.get_one(currency=currency).current_members_count

    def last_members_count(self, currency):
        """
        Get the last ud value and base
        :rtype: int, int
        """
        return self._repo.get_one(currency=currency).last_members_count

    def last_ud(self, currency):
        """
        Get the last ud value and base
        :rtype: int, int
        """
        blockchain = self._repo.get_one(currency=currency)
        try:
            return blockchain.last_ud, blockchain.last_ud_base
        except AttributeError:
            pass

    def last_ud_time(self, currency):
        """
        Get the last ud time
        :rtype: int
        """
        blockchain = self._repo.get_one(currency=currency)
        return blockchain.last_ud_time

    def previous_monetary_mass(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one(currency=currency).previous_mass

    def previous_members_count(self, currency):
        """
        Get the local current monetary mass
        :rtype: int
        """
        return self._repo.get_one(currency=currency).previous_members_count

    def previous_ud(self, currency):
        """
        Get the previous ud value and base
        :rtype: int, int
        """
        blockchain = self._repo.get_one(currency=currency)
        return blockchain.previous_ud, blockchain.previous_ud_base

    def previous_ud_time(self, currency):
        """
        Get the previous ud time
        :rtype: int
        """
        blockchain = self._repo.get_one(currency=currency)
        return blockchain.previous_ud_time

    async def get_block(self, currency, number):
        """
        Get block documen at a given number
        :param str currency:
        :param int number:
        :rtype: duniterpy.documents.Block
        """
        block = await self._bma_connector.get(currency, bma.blockchain.block, req_args={'number': number})
        if block:
            block_doc = Block.from_signed_raw("{0}{1}\n".format(block['raw'], block['signature']))
            return block_doc

    async def new_blocks_with_identities(self, currency):
        """
        Get blocks more recent than local blockuid
        with identities
        """
        with_identities = []
        future_requests = []
        for req in (bma.blockchain.joiners,
                    bma.blockchain.leavers,
                    bma.blockchain.actives,
                    bma.blockchain.excluded,
                    bma.blockchain.newcomers):
            future_requests.append(self._bma_connector.get(currency, req))
        results = await asyncio.gather(*future_requests)

        for res in results:
            with_identities += res["result"]["blocks"]

        local_current_buid = self.current_buid(currency)
        return sorted([b for b in with_identities if b > local_current_buid.number])

    async def new_blocks_with_money(self, currency):
        """
        Get blocks more recent than local block uid
        with money data (tx and uds)
        """
        with_money = []
        future_requests = []
        for req in (bma.blockchain.ud, bma.blockchain.tx):
            future_requests.append(self._bma_connector.get(currency, req))
        results = await asyncio.gather(*future_requests)

        for res in results:
            with_money += res["result"]["blocks"]

        local_current_buid = self.current_buid(currency)
        return sorted([b for b in with_money if b > local_current_buid.number])

    async def next_blocks(self, start, filter, currency):
        """
        Get blocks from the network
        :param List[int] numbers: list of blocks numbers to get
        :return: the list of block documents
        :rtype: List[duniterpy.documents.Block]
        """
        blocks = []
        blocks_data = await self._bma_connector.get(currency, bma.blockchain.blocks, req_args={'count': 100,
                                                                                 'start': start})
        for data in blocks_data:
            if data['number'] in filter or data['number'] == start+99:
                blocks.append(Block.from_signed_raw(data["raw"] + data["signature"] + "\n"))

        return blocks

    async def initialize_blockchain(self, currency, log_stream):
        """
        Initialize blockchain for a given currency if no source exists locally
        """
        blockchain = self._repo.get_one(currency=currency)
        if not blockchain:
            blockchain = Blockchain(currency=currency)
            log_stream("Requesting blockchain parameters")
            try:
                parameters = await self._bma_connector.get(currency, bma.blockchain.parameters)
                blockchain.parameters.ms_validity = parameters['msValidity']
                blockchain.parameters.avg_gen_time = parameters['avgGenTime']
                blockchain.parameters.c = parameters['c']
                blockchain.parameters.dt = parameters['dt']
                blockchain.parameters.dt_diff_eval = parameters['dtDiffEval']
                blockchain.parameters.median_time_blocks = parameters['medianTimeBlocks']
                blockchain.parameters.percent_rot = parameters['percentRot']
                blockchain.parameters.idty_window = parameters['idtyWindow']
                blockchain.parameters.ms_window = parameters['msWindow']
                blockchain.parameters.sig_window = parameters['sigWindow']
                blockchain.parameters.sig_period = parameters['sigPeriod']
                blockchain.parameters.sig_qty = parameters['sigQty']
                blockchain.parameters.sig_stock = parameters['sigStock']
                blockchain.parameters.sig_validity = parameters['sigValidity']
                blockchain.parameters.sig_qty = parameters['sigQty']
                blockchain.parameters.sig_period = parameters['sigPeriod']
                blockchain.parameters.ud0 = parameters['ud0']
                blockchain.parameters.xpercent = parameters['xpercent']
            except errors.DuniterError as e:
                raise

        log_stream("Requesting current block")
        try:
            current_block = await self._bma_connector.get(currency, bma.blockchain.current)
            signed_raw = "{0}{1}\n".format(current_block['raw'], current_block['signature'])
            block = Block.from_signed_raw(signed_raw)
            blockchain.current_buid = block.blockUID
            blockchain.median_time = block.mediantime
            blockchain.current_members_count = block.members_count
        except errors.DuniterError as e:
            if e.ucode != errors.NO_CURRENT_BLOCK:
                raise

        log_stream("Requesting blocks with dividend")
        with_ud = await self._bma_connector.get(currency, bma.blockchain.ud)
        blocks_with_ud = with_ud['result']['blocks']

        if len(blocks_with_ud) > 0:
            log_stream("Requesting last block with dividend")
            try:
                index = max(len(blocks_with_ud) - 1, 0)
                block_number = blocks_with_ud[index]
                block_with_ud = await self._bma_connector.get(currency, bma.blockchain.block,
                                                              req_args={'number': block_number})
                if block_with_ud:
                    blockchain.last_members_count = block_with_ud['membersCount']
                    blockchain.last_ud = block_with_ud['dividend']
                    blockchain.last_ud_base = block_with_ud['unitbase']
                    blockchain.last_ud_time = block_with_ud['medianTime']
                    blockchain.current_mass = block_with_ud['monetaryMass']
            except errors.DuniterError as e:
                if e.ucode != errors.NO_CURRENT_BLOCK:
                    raise

            log_stream("Requesting previous block with dividend")
            try:
                index = max(len(blocks_with_ud) - 2, 0)
                block_number = blocks_with_ud[index]
                block_with_ud = await self._bma_connector.get(currency, bma.blockchain.block,
                                                              req_args={'number': block_number})
                blockchain.previous_mass = block_with_ud['monetaryMass']
                blockchain.previous_members_count = block_with_ud['membersCount']
                blockchain.previous_ud = block_with_ud['dividend']
                blockchain.previous_ud_base = block_with_ud['unitbase']
                blockchain.previous_ud_time = block_with_ud['medianTime']
            except errors.DuniterError as e:
                if e.ucode != errors.NO_CURRENT_BLOCK:
                    raise

        try:
            self._repo.insert(blockchain)
        except sqlite3.IntegrityError:
            self._repo.update(blockchain)

    def handle_new_blocks(self, currency, blocks):
        """
        Initialize blockchain for a given currency if no source exists locally
        :param List[duniterpy.documents.Block] blocks
        """
        blockchain = self._repo.get_one(currency=currency)
        for block in sorted(blocks):
            if blockchain.current_buid < block.blockUID:
                blockchain.current_buid = block.blockUID
                blockchain.median_time = block.mediantime
                blockchain.current_members_count = block.members_count
                if block.ud:
                    blockchain.previous_mass = blockchain.current_mass
                    blockchain.previous_members_count = blockchain.last_members_count
                    blockchain.previous_ud = blockchain.last_ud
                    blockchain.previous_ud_base = blockchain.last_ud_base
                    blockchain.previous_ud_time = blockchain.last_ud_time
                    blockchain.current_mass += (block.ud * 10**block.unit_base) * block.members_count
                    blockchain.last_members_count = block.members_count
                    blockchain.last_ud = block.ud
                    blockchain.last_ud_base = block.unit_base
                    blockchain.last_ud_time = block.mediantime
        self._repo.update(blockchain)

    def remove_blockchain(self, currency):
        self._repo.drop(self._repo.get_one(currency=currency))

