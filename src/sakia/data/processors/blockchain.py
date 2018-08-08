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
    _repo = attr.ib()  # :type sakia.data.repositories.BlockchainsRepo
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

    async def ud_before(self, currency, block_number, udblocks=[]):
        """

        :param currency:
        :param block_number:
        :param udblocks: /blockchain/ud/history data of given key
        :return:
        """
        try:
            if not udblocks:
                udblocks = await self._bma_connector.get(currency, bma.blockchain.ud)
            udblocks = udblocks['result']['blocks']
            ud_block_number = next(b for b in udblocks if b <= block_number)
            block = await self._bma_connector.get(currency, bma.blockchain.block, {'number': ud_block_number})
            return block['dividend'], block['unitbase']
        except StopIteration:
            self._logger.debug("No dividend generated before {0}".format(block_number))
        except NoPeerAvailable as e:
            self._logger.debug(str(e))
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                self._logger.debug(str(e))
            else:
                raise
        return 0, 0

    def adjusted_ts(self, currency, timestamp):
        parameters = self.parameters(currency)
        return timestamp + parameters.median_time_blocks/2 * parameters.avg_gen_time

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

    def rounded_timestamp(self, currency, block_number):
        parameters = self.parameters(currency)
        current_time = self.time(currency)
        current_block = self.current_buid(currency)
        diff_blocks = block_number - current_block.number
        diff_time = diff_blocks * parameters.avg_gen_time
        return current_time + diff_time

    def block_number_30days_ago(self, currency, blockstamp):
        """
        When refreshing data, we only request the last 30 days
        This method computes the block number 30 days ago
        :param currency:
        :return:
        """
        avg_blocks_per_month = int(30 * 24 * 3600 / self.parameters(currency).avg_gen_time)
        return blockstamp.number - avg_blocks_per_month

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

    def last_mass(self, currency):
        """
        Get the last ud value and base
        :rtype: int, int
        """
        return self._repo.get_one(currency=currency).last_mass

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

    async def initialize_blockchain(self, currency):
        """
        Initialize blockchain for a given currency if no source exists locally
        """
        blockchain = self._repo.get_one(currency=currency)
        if not blockchain:
            blockchain = Blockchain(currency=currency)
            self._logger.debug("Requesting blockchain parameters")
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
                blockchain.parameters.ud_time_0 = parameters['udTime0']
                blockchain.parameters.dt_reeval = parameters['dtReeval']
                blockchain.parameters.ud_reeval_time_0 = parameters['udReevalTime0']
                blockchain.parameters.xpercent = parameters['xpercent']
            except errors.DuniterError as e:
                raise

        self._logger.debug("Requesting current block")
        try:
            current_block = await self._bma_connector.get(currency, bma.blockchain.current)
            signed_raw = "{0}{1}\n".format(current_block['raw'], current_block['signature'])
            block = Block.from_signed_raw(signed_raw)
            blockchain.current_buid = block.blockUID
            blockchain.median_time = block.mediantime
            blockchain.current_members_count = block.members_count
            blockchain.current_mass = current_block['monetaryMass']
        except errors.DuniterError as e:
            if e.ucode != errors.NO_CURRENT_BLOCK:
                raise
        await self.refresh_dividend_data(currency, blockchain)

        try:
            self._repo.insert(blockchain)
        except sqlite3.IntegrityError:
            self._repo.update(blockchain)

    async def refresh_dividend_data(self, currency, blockchain):
        self._logger.debug("Requesting blocks with dividend")
        with_ud = await self._bma_connector.get(currency, bma.blockchain.ud)
        blocks_with_ud = with_ud['result']['blocks']

        if len(blocks_with_ud) > 0:
            self._logger.debug("Requesting last block with dividend")
            try:
                nb_previous_reevaluations = int((blockchain.median_time - blockchain.parameters.ud_reeval_time_0)
                                                / blockchain.parameters.dt_reeval)

                last_reeval_offset = (blockchain.median_time -
                                      (blockchain.parameters.ud_reeval_time_0 +
                                       nb_previous_reevaluations * blockchain.parameters.dt_reeval)
                                      )

                dt_reeval_block_target = max(blockchain.current_buid.number - int(last_reeval_offset
                                                                                  / blockchain.parameters.avg_gen_time),
                                             0)
                try:
                    last_ud_reeval_block_number = [b for b in blocks_with_ud if b <= dt_reeval_block_target][-1]
                except IndexError:
                    last_ud_reeval_block_number = 0

                if last_ud_reeval_block_number:
                    block_with_ud = await self._bma_connector.get(currency, bma.blockchain.block,
                                                                  req_args={'number': last_ud_reeval_block_number})
                    if block_with_ud:
                        blockchain.last_members_count = block_with_ud['membersCount']
                        blockchain.last_ud = block_with_ud['dividend']
                        blockchain.last_ud_base = block_with_ud['unitbase']
                        blockchain.last_ud_time = block_with_ud['medianTime']
                        blockchain.last_mass = block_with_ud['monetaryMass']

                    self._logger.debug("Requesting previous block with dividend")
                    dt_reeval_block_target = max(dt_reeval_block_target - int(blockchain.parameters.dt_reeval
                                                                              / blockchain.parameters.avg_gen_time),
                                                 0)

                    try:
                        previous_ud_reeval_block_number = [b for b in blocks_with_ud if b <= dt_reeval_block_target][-1]
                    except IndexError:
                        previous_ud_reeval_block_number = min(blocks_with_ud)

                    block_with_ud = await self._bma_connector.get(currency, bma.blockchain.block,
                                                                  req_args={'number': previous_ud_reeval_block_number})
                    blockchain.previous_mass = block_with_ud['monetaryMass']
                    blockchain.previous_members_count = block_with_ud['membersCount']
                    blockchain.previous_ud = block_with_ud['dividend']
                    blockchain.previous_ud_base = block_with_ud['unitbase']
                    blockchain.previous_ud_time = block_with_ud['medianTime']
            except errors.DuniterError as e:
                if e.ucode != errors.NO_CURRENT_BLOCK:
                    raise

    async def handle_new_blocks(self, currency, network_blockstamp):
        """
        Initialize blockchain for a given currency if no source exists locally
        :param str currency:
        :param BlockUID network_blockstamp: the blockstamp of the network
        """

        self._logger.debug("Requesting current block")
        try:
            current_block = await self._bma_connector.get(currency, bma.blockchain.block,
                                                                  req_args={'number': network_blockstamp.number})
            signed_raw = "{0}{1}\n".format(current_block['raw'], current_block['signature'])
            block = Block.from_signed_raw(signed_raw)
            blockchain = self._repo.get_one(currency=currency)
            blockchain.current_buid = block.blockUID
            blockchain.median_time = block.mediantime
            blockchain.current_members_count = block.members_count

            if blockchain.last_ud_time + blockchain.parameters.dt <= blockchain.median_time:
                await self.refresh_dividend_data(currency, blockchain)

            self._repo.update(blockchain)

        except errors.DuniterError as e:
            if e.ucode != errors.NO_CURRENT_BLOCK:
                raise


    def remove_blockchain(self, currency):
        self._repo.drop(self._repo.get_one(currency=currency))

