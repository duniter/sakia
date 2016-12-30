import attr
import re
from ..entities import Source
from .nodes import NodesProcessor
from ..connectors import BmaConnector
from duniterpy.api import bma, errors
import asyncio


@attr.s
class SourcesProcessor:
    """
    :param sakia.data.repositories.SourcesRepo _repo: the repository of the sources
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
        return cls(app.db.sources_repo,
                   BmaConnector(NodesProcessor(app.db.nodes_repo)))

    async def initialize_sources(self, currency, pubkey, log_stream):
        """
        Initialize sources for a given pubkey if no source exists locally
        """
        one_source = self._repo.get_one(currency=currency)
        if not one_source:
            log_stream("Requesting sources")
            try:
                sources_data = await self._bma_connector.get(currency, bma.tx.sources,
                                                             req_args={'pubkey': pubkey})

                log_stream("Found {0} sources".format(len(sources_data['sources'])))
                for i, s in enumerate(sources_data['sources']):
                    source = Source(currency=currency, pubkey=pubkey,
                                    identifier=s['identifier'],
                                    type=s['type'],
                                    noffset=s['noffset'],
                                    amount=s['amount'],
                                    base=s['base'])
                    self._repo.insert(source)
                    await asyncio.sleep(0)
                    log_stream("{0}/{1} sources".format(i, len(sources_data['sources'])))
            except errors.DuniterError as e:
                raise

    def amount(self, currency, pubkey):
        """
        Get the amount value of the sources for a given pubkey
        :param str currency: the currency of the sources
        :param str pubkey: the pubkey owning the sources
        :return:
        """
        sources = self._repo.get_all(currency=currency, pubkey=pubkey)
        return sum([s.amount * (10**s.base) for s in sources])

    def available(self, currency):
        """"
        :param str currency: the currency of the sources
        :rtype: list[sakia.data.entities.Source]
        """
        return self._repo.get_all(currency=currency)

    def consume(self, sources):
        """

        :param currency:
        :param sources:
        :return:
        """
        for s in sources:
            self._repo.drop(s)