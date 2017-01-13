from PyQt5.QtCore import QObject
from duniterpy.api import bma, errors
import logging
from sakia.data.entities import Source


class SourcesServices(QObject):
    """
    Source service is managing sources received
    to update data locally
    """
    def __init__(self, currency, sources_processor, connections_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.SourcesProcessor sources_processor: the sources processor for given currency
        :param sakia.data.processors.ConnectionsProcessor connections_processor: the connections processor
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._sources_processor = sources_processor
        self._connections_processor = connections_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    def amount(self, pubkey):
        return self._sources_processor.amount(self.currency, pubkey)

    async def refresh_sources(self):
        connections_pubkeys = [c.pubkey for c in self._connections_processor.connections_to(self.currency)]
        for pubkey in connections_pubkeys:
            sources_data = await self._bma_connector.get(self.currency, bma.tx.sources,
                                                         req_args={'pubkey': pubkey})

            self._logger.debug("Found {0} sources".format(len(sources_data['sources'])))
            self._sources_processor.drop_all_of(currency=self.currency, pubkey=pubkey)
            for i, s in enumerate(sources_data['sources']):
                source = Source(currency=self.currency, pubkey=pubkey,
                                identifier=s['identifier'],
                                type=s['type'],
                                noffset=s['noffset'],
                                amount=s['amount'],
                                base=s['base'])
                self._sources_processor.commit(source)
                self._logger.debug("{0}/{1} sources".format(i, len(sources_data['sources'])))
