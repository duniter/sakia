from PyQt5.QtCore import QObject
from duniterpy.api import bma
import math
import logging


class SourcesServices(QObject):
    """
    Source service is managing sources received
    to update data locally
    """
    def __init__(self, currency, sources_processor, bma_connector):
        """
        Constructor the identities service

        :param str currency: The currency name of the community
        :param sakia.data.processors.SourceProcessor sources_processor: the sources processor for given currency
        :param sakia.data.connectors.BmaConnector bma_connector: The connector to BMA API
        """
        super().__init__()
        self._sources_processor = sources_processor
        self._bma_connector = bma_connector
        self.currency = currency
        self._logger = logging.getLogger('sakia')

    def amount(self, pubkey):
        return self._sources_processor.amount(self.currency, pubkey)
