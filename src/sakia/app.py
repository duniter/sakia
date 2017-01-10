import attr
import datetime
import logging

import aiohttp
from PyQt5.QtCore import QObject, pyqtSignal, QTranslator, QCoreApplication, QLocale
from aiohttp.connector import ProxyConnector

from . import __version__
from .options import SakiaOptions
from sakia.data.connectors import BmaConnector
from sakia.services import NetworkService, BlockchainService, IdentitiesService, \
    SourcesServices, TransactionsService, DocumentsService
from sakia.data.repositories import SakiaDatabase
from sakia.data.entities import Transaction, Connection, Identity
from sakia.data.processors import BlockchainProcessor, NodesProcessor, IdentitiesProcessor, \
    CertificationsProcessor, SourcesProcessor, TransactionsProcessor, ConnectionsProcessor, DividendsProcessor
from sakia.data.files import AppDataFile, UserParametersFile
from sakia.decorators import asyncify
from sakia.money import *


@attr.s()
class Application(QObject):

    """
    Managing core application datas :
    Accounts list and general configuration
    Saving and loading the application state


    :param QCoreApplication qapp: Qt Application
    :param quamash.QEventLoop loop: quamash.QEventLoop instance
    :param sakia.options.SakiaOptions options: the options
    :param sakia.data.entities.AppData app_data: the application data
    :param sakia.data.entities.UserParameters parameters: the application current user parameters
    :param sakia.data.repositories.SakiaDatabase db: The database
    :param dict network_services: All network services for current currency
    :param dict blockchain_services: All blockchain services for current currency
    :param dict identities_services: All identities services for current currency
    :param dict sources_services: All sources services for current currency
    :param dict transactions_services: All transactions services for current currency
    :param sakia.services.DocumentsService documents_service: A service to broadcast documents
    """

    new_transfer = pyqtSignal(Transaction)
    transaction_state_changed = pyqtSignal(Transaction)
    identity_changed = pyqtSignal(Identity)
    new_connection = pyqtSignal(Connection)
    referential_changed = pyqtSignal()

    qapp = attr.ib()
    loop = attr.ib()
    options = attr.ib()
    app_data = attr.ib()
    parameters = attr.ib()
    db = attr.ib()
    network_services = attr.ib(default=attr.Factory(dict))
    blockchain_services = attr.ib(default=attr.Factory(dict))
    identities_services = attr.ib(default=attr.Factory(dict))
    sources_services = attr.ib(default=attr.Factory(dict))
    transactions_services = attr.ib(default=attr.Factory(dict))
    documents_service = attr.ib(default=None)
    current_ref = attr.ib(default=Relative)
    _logger = attr.ib(default=attr.Factory(lambda:logging.getLogger('sakia')))
    available_version = attr.ib(init=False)
    _translator = attr.ib(init=False)

    def __attrs_post_init__(self):
        super().__init__()
        self._translator = QTranslator(self.qapp)
        self.available_version = True, __version__, ""

    @classmethod
    def startup(cls, argv, qapp, loop):
        options = SakiaOptions.from_arguments(argv)
        app_data = AppDataFile.in_config_path(options.config_path).load_or_init()
        app = cls(qapp, loop, options, app_data, None, None)
        #app.set_proxy()
        app.get_last_version()
        app.load_profile(app_data.default)
        app.start_coroutines()
        app.documents_service = DocumentsService.instanciate(app)
        app.switch_language()
        return app

    def load_profile(self, profile_name):
        """
        Initialize databases depending on profile loaded
        :param profile_name:
        :return:
        """
        self.parameters = UserParametersFile.in_config_path(self.options.config_path, profile_name).load_or_init()
        self.db = SakiaDatabase.load_or_init(self.options.config_path, profile_name)

        self.instanciate_services()

    def instanciate_services(self):
        nodes_processor = NodesProcessor(self.db.nodes_repo)
        bma_connector = BmaConnector(nodes_processor, self.parameters)
        connections_processor = ConnectionsProcessor(self.db.connections_repo)
        identities_processor = IdentitiesProcessor(self.db.identities_repo, self.db.blockchains_repo, bma_connector)
        certs_processor = CertificationsProcessor(self.db.certifications_repo, self.db.identities_repo, bma_connector)
        blockchain_processor = BlockchainProcessor.instanciate(self)
        sources_processor = SourcesProcessor.instanciate(self)
        transactions_processor = TransactionsProcessor.instanciate(self)
        dividends_processor = DividendsProcessor.instanciate(self)

        self.blockchain_services = {}
        self.network_services = {}
        self.identities_services = {}
        self.sources_services = {}
        self.transactions_services = {}
        self.documents_service = DocumentsService.instanciate(self)

        for currency in self.db.connections_repo.get_currencies():
            if currency not in self.identities_services:
                self.identities_services[currency] = IdentitiesService(currency, connections_processor,
                                                                   identities_processor,
                                                                   certs_processor, blockchain_processor,
                                                                   bma_connector)

            if currency not in self.transactions_services:
                self.transactions_services[currency] = TransactionsService(currency, transactions_processor,
                                                                           dividends_processor,
                                                                           identities_processor, connections_processor,
                                                                           bma_connector)

            if currency not in self.blockchain_services:
                self.blockchain_services[currency] = BlockchainService(self, currency, blockchain_processor, bma_connector,
                                                                   self.identities_services[currency],
                                                                   self.transactions_services[currency])

            if currency not in self.network_services:
                self.network_services[currency] = NetworkService.load(self, currency, nodes_processor,
                                                                  self.blockchain_services[currency])
            if currency not in self.sources_services:
                self.sources_services[currency] = SourcesServices(currency, sources_processor, bma_connector)

    def switch_language(self):
        logging.debug("Loading translations")
        locale = self.parameters.lang
        QLocale.setDefault(QLocale(locale))
        QCoreApplication.removeTranslator(self._translator)
        self._translator = QTranslator(self.qapp)
        if locale == "en_GB":
            QCoreApplication.installTranslator(self._translator)
        elif self._translator.load(":/i18n/{0}".format(locale)):
            if QCoreApplication.installTranslator(self._translator):
                logging.debug("Loaded i18n/{0}".format(locale))
            else:
                logging.debug("Couldn't load translation")

    def start_coroutines(self):
        for currency in self.db.connections_repo.get_currencies():
            self.network_services[currency].start_coroutines()

    async def stop_current_profile(self, closing=False):
        """
        Save the account to the cache
        and stop the coroutines
        """
        for currency in self.db.connections_repo.get_currencies():
            await self.network_services[currency].stop_coroutines(closing)

    @asyncify
    async def get_last_version(self):
        try:
            with aiohttp.ClientSession() as session:
                with aiohttp.Timeout(15):
                    response = await session.get("https://api.github.com/repos/duniter/sakia/releases",
                                                 proxy=self.parameters.proxy())
                    if response.status == 200:
                        releases = await response.json()
                        latest = None
                        for r in releases:
                            if not latest:
                                latest = r
                            else:
                                latest_date = datetime.datetime.strptime(latest['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                                date = datetime.datetime.strptime(r['published_at'], "%Y-%m-%dT%H:%M:%SZ")
                                if latest_date < date:
                                    latest = r
                        latest_version = latest["tag_name"]
                        version = (__version__ == latest_version,
                                   latest_version,
                                   latest["html_url"])
                        logging.debug("Found version : {0}".format(latest_version))
                        logging.debug("Current version : {0}".format(__version__))
                        self.available_version = version
        except (aiohttp.errors.ClientError, aiohttp.errors.TimeoutError) as e:
            self._logger.debug("Could not connect to github : {0}".format(str(e)))

    def save_parameters(self, parameters):
        self.parameters = UserParametersFile\
            .in_config_path(self.options.config_path, parameters.profile_name)\
            .save(parameters)

    def change_referential(self, index):
        self.current_ref = Referentials[index]
        self.referential_changed.emit()

    def connection_exists(self):
        return len(ConnectionsProcessor.instanciate(self).connections()) > 0
