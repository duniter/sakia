import attr
import re
from ..entities import Dividend
from .nodes import NodesProcessor
from ..connectors import BmaConnector
from duniterpy.api import bma, errors
from duniterpy.documents import Transaction
import asyncio
import sqlite3


@attr.s
class DividendsProcessor:
    """
    :param sakia.data.repositories.DividendsRepo _repo: the repository of the sources
    :param sakia.data.connectors.bma.BmaConnector _bma_connector: the bma connector
    """
    _repo = attr.ib()
    _bma_connector = attr.ib()

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.dividends_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters))

    def commit(self, dividend):
        try:
            self._repo.insert(dividend)
        except sqlite3.IntegrityError:
            self._logger.debug("Dividend already in db")

    async def initialize_dividends(self, identity, transactions, log_stream):
        """
        Request transactions from the network to initialize data for a given pubkey
        :param sakia.data.entities.Identity identity:
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx processor
        :param function log_stream:
        """
        history_data = await self._bma_connector.get(identity.currency, bma.ud.history,
                                                     req_args={'pubkey': identity.pubkey})
        log_stream("Found {0} available dividends".format(len(history_data["history"]["history"])))
        block_numbers = []
        for ud_data in history_data["history"]["history"]:
            dividend = Dividend(currency=identity.currency,
                                pubkey=identity.pubkey,
                                block_number=ud_data["block_number"],
                                timestamp=ud_data["time"],
                                amount=ud_data["amount"],
                                base=ud_data["base"])
            log_stream("Dividend of block {0}".format(dividend.block_number))
            block_numbers.append(dividend.block_number)
            try:
                self._repo.insert(dividend)
            except sqlite3.IntegrityError:
                log_stream("Dividend already registered in database")

        for tx in transactions:
            txdoc = Transaction.from_signed_raw(tx.raw)
            for input in txdoc.inputs:
                if input.source == "D" and input.origin_id == identity.pubkey and input.index not in block_numbers:
                    block = await self._bma_connector.get(identity.currency,
                                                          bma.blockchain.block, req_args={'number': input.index})

                    dividend = Dividend(currency=identity.currency,
                                        pubkey=identity.pubkey,
                                        block_number=input.index,
                                        timestamp=block["medianTime"],
                                        amount=block["dividend"],
                                        base=block["unitbase"])
                    log_stream("Dividend of block {0}".format(dividend.block_number))
                    try:
                        self._repo.insert(dividend)
                    except sqlite3.IntegrityError:
                        log_stream("Dividend already registered in database")

    def dividends(self, currency, pubkey):
        return self._repo.get_all(currency=currency, pubkey=pubkey)