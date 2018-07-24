import attr
import logging
from ..entities import Dividend
from .nodes import NodesProcessor
from ..connectors import BmaConnector
from duniterpy.api import bma
from duniterpy.documents import Transaction
import sqlite3
import asyncio


@attr.s
class DividendsProcessor:
    """
    :param sakia.data.repositories.DividendsRepo _repo: the repository of the sources
    :param sakia.data.repositories.BlockchainsRepo _blockchain_repo: the repository of the sources
    :param sakia.data.connectors.bma.BmaConnector _bma_connector: the bma connector
    """
    _repo = attr.ib()
    _blockchain_repo = attr.ib()
    _bma_connector = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.dividends_repo, app.db.blockchains_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters))

    def commit(self, dividend):
        try:
            self._repo.insert(dividend)
            return True
        except sqlite3.IntegrityError:
            self._logger.debug("Dividend already in db")
        return False

    async def initialize_dividends(self, connection, transactions, log_stream, progress):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param sakia.data.entities.Connection connection:
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx processor
        :param function log_stream:
        :param function progress: progress callback
        """
        blockchain = self._blockchain_repo.get_one(currency=connection.currency)
        avg_blocks_per_month = int(30 * 24 * 3600 / blockchain.parameters.avg_gen_time)
        start = blockchain.current_buid.number - avg_blocks_per_month
        history_data = await self._bma_connector.get(connection.currency, bma.ud.history,
                                                     req_args={'pubkey': connection.pubkey})
        block_numbers = []
        dividends = []
        for ud_data in history_data["history"]["history"]:
            if ud_data["block_number"] > start:
                dividend = Dividend(currency=connection.currency,
                                    pubkey=connection.pubkey,
                                    block_number=ud_data["block_number"],
                                    timestamp=ud_data["time"],
                                    amount=ud_data["amount"],
                                    base=ud_data["base"])
                log_stream("Dividend of block {0}".format(dividend.block_number))
                block_numbers.append(dividend.block_number)
                try:
                    dividends.append(dividend)
                    self._repo.insert(dividend)
                except sqlite3.IntegrityError:
                    log_stream("Dividend already registered in database")

        for tx in transactions:
            txdoc = Transaction.from_signed_raw(tx.raw)
            for input in txdoc.inputs:
                if input.source == "D" and input.origin_id == connection.pubkey \
                        and input.index not in block_numbers and input.index > start:
                    diff_blocks = blockchain.current_buid.number - input.index
                    ud_mediantime = blockchain.median_time - diff_blocks*blockchain.parameters.avg_gen_time
                    dividend = Dividend(currency=connection.currency,
                                        pubkey=connection.pubkey,
                                        block_number=input.index,
                                        timestamp=ud_mediantime,
                                        amount=input.amount,
                                        base=input.base)
                    log_stream("Dividend of block {0}".format(dividend.block_number))
                    try:
                        dividends.append(dividend)
                        self._repo.insert(dividend)
                    except sqlite3.IntegrityError:
                        log_stream("Dividend already registered in database")
        return dividends

    def dividends(self, currency, pubkey):
        return self._repo.get_all(currency=currency, pubkey=pubkey)

    def cleanup_connection(self, connection):
        """
        Cleanup connection after removal
        :param sakia.data.entities.Connection connection:
        :return:
        """
        dividends = self._repo.get_all(currency=connection.currency, pubkey=connection.pubkey)
        for d in dividends:
            self._repo.drop(d)
