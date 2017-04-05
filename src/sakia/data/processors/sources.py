import attr
import sqlite3
import logging
from ..entities import Source
from .nodes import NodesProcessor
from ..connectors import BmaConnector
from duniterpy.api import bma, errors


@attr.s
class SourcesProcessor:
    """
    :param sakia.data.repositories.SourcesRepo _repo: the repository of the sources
    :param sakia.data.connectors.bma.BmaConnector _bma_connector: the bma connector
    """
    _repo = attr.ib()
    _bma_connector = attr.ib()
    _logger = attr.ib(default=attr.Factory(lambda: logging.getLogger('sakia')))

    @classmethod
    def instanciate(cls, app):
        """
        Instanciate a blockchain processor
        :param sakia.app.Application app: the app
        """
        return cls(app.db.sources_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo), app.parameters))

    def commit(self, source):
        try:
            self._repo.insert(source)
        except sqlite3.IntegrityError:
            self._logger.debug("Source already known : {0}".format(source.identifier))

    def amount(self, currency, pubkey):
        """
        Get the amount value of the sources for a given pubkey
        :param str currency: the currency of the sources
        :param str pubkey: the pubkey owning the sources
        :return:
        """
        sources = self._repo.get_all(currency=currency, pubkey=pubkey)
        return sum([s.amount * (10**s.base) for s in sources])

    def available(self, currency, pubkey):
        """"
        :param str currency: the currency of the sources
        :param str pubkey: the owner of the sources
        :rtype: list[sakia.data.entities.Source]
        """
        return self._repo.get_all(currency=currency, pubkey=pubkey)

    def consume(self, sources):
        """

        :param currency:
        :param sources:
        :return:
        """
        for s in sources:
            self._repo.drop(s)

    def insert(self, source):
        try:
            self._repo.insert(source)
        except sqlite3.IntegrityError:
            self._logger.debug("Source already exist : {0}".format(source))

    def drop(self, source):
        try:
            self._repo.drop(source)
        except sqlite3.IntegrityError:
            self._logger.debug("Source already dropped : {0}".format(source))

    def drop_all_of(self, currency, pubkey):
        self._repo.drop_all(currency=currency, pubkey=pubkey)
