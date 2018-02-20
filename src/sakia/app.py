import attr
import datetime
import logging
import socket
import sakia.i18n_rc
import async_timeout
import aiohttp
from PyQt5.QtCore import QObject, pyqtSignal, QTranslator, QCoreApplication, QLocale, Qt
from . import __version__
from .options import SakiaOptions
from sakia.data.connectors import BmaConnector
from sakia.services import NetworkService, BlockchainService, IdentitiesService, \
    SourcesServices, TransactionsService, DocumentsService
from sakia.data.repositories import SakiaDatabase
from sakia.data.entities import Transaction, Connection, Identity, Dividend
from sakia.data.processors import BlockchainProcessor, NodesProcessor, IdentitiesProcessor, \
    CertificationsProcessor, SourcesProcessor, TransactionsProcessor, ConnectionsProcessor, DividendsProcessor
from sakia.data.files import AppDataFile, UserParametersFile, PluginsDirectory
from sakia.decorators import asyncify
from sakia.money import *
import asyncio


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
    :param sakia.services.NetworkService network_service: All network services for current currency
    :param sakia.services.BlockchainService blockchain_service: All blockchain services for current currency
    :param sakia.services.IdentitiesService identities_service: All identities services for current currency
    :param sakia.services.SourcesService sources_service: All sources services for current currency
    :param sakia.Services.TransactionsService transactions_service: All transactions services for current currency
    :param sakia.services.DocumentsService documents_service: A service to broadcast documents
    """

    new_dividend = pyqtSignal(Connection, Dividend)
    new_transfer = pyqtSignal(Connection, Transaction)
    transaction_state_changed = pyqtSignal(Transaction)
    identity_changed = pyqtSignal(Identity)
    new_connection = pyqtSignal(Connection)
    connection_removed = pyqtSignal(Connection)
    referential_changed = pyqtSignal()
    sources_refreshed = pyqtSignal()
    new_blocks_handled = pyqtSignal()
    view_in_wot = pyqtSignal(Identity)
    refresh_started = pyqtSignal()
    refresh_finished = pyqtSignal()

    qapp = attr.ib()
    loop = attr.ib()
    options = attr.ib()
    app_data = attr.ib()
    parameters = attr.ib()
    db = attr.ib()
    currency = attr.ib()
    plugins_dir = attr.ib()
    network_service = attr.ib(default=None)
    blockchain_service = attr.ib(default=None)
    identities_service = attr.ib(default=None)
    sources_service = attr.ib(default=None)
    transactions_service = attr.ib(default=None)
    documents_service = attr.ib(default=None)
    current_ref = attr.ib(default=Quantitative)
    _logger = attr.ib(default=attr.Factory(lambda:logging.getLogger('sakia')))
    available_version = attr.ib(init=False)
    _translator = attr.ib(init=False)

    def __attrs_post_init__(self):
        super().__init__()
        self._translator = QTranslator(self.qapp)
        self.available_version = True, __version__, ""

    @classmethod
    def startup(cls, argv, qapp, loop):
        qapp.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        options = SakiaOptions.from_arguments(argv)
        app_data = AppDataFile.in_config_path(options.config_path).load_or_init()
        app = cls(qapp, loop, options, app_data, None, None, options.currency, None)
        #app.set_proxy()
        app.load_profile(options.profile)
        app.documents_service = DocumentsService.instanciate(app)
        app.switch_language()
        return app

    def load_profile(self, profile_name):
        """
        Initialize databases depending on profile loaded
        :param profile_name:
        :return:
        """
        self.plugins_dir = PluginsDirectory.in_config_path(self.options.config_path, profile_name).load_or_init(self.options.with_plugin)
        self.parameters = UserParametersFile.in_config_path(self.options.config_path, profile_name).load_or_init(profile_name)
        self.db = SakiaDatabase.load_or_init(self.options, profile_name)

        self.instanciate_services()

    def instanciate_services(self):
        nodes_processor = NodesProcessor(self.db.nodes_repo)
        bma_connector = BmaConnector(nodes_processor, self.parameters)
        connections_processor = ConnectionsProcessor(self.db.connections_repo)
        identities_processor = IdentitiesProcessor(self.db.identities_repo, self.db.certifications_repo, self.db.blockchains_repo, bma_connector)
        certs_processor = CertificationsProcessor(self.db.certifications_repo, self.db.identities_repo, bma_connector)
        blockchain_processor = BlockchainProcessor.instanciate(self)
        sources_processor = SourcesProcessor.instanciate(self)
        transactions_processor = TransactionsProcessor.instanciate(self)
        dividends_processor = DividendsProcessor.instanciate(self)
        nodes_processor.initialize_root_nodes(self.currency)
        self.db.commit()

        self.documents_service = DocumentsService.instanciate(self)
        self.identities_service = IdentitiesService(self.currency, connections_processor,
                                                    identities_processor,
                                                    certs_processor, blockchain_processor,
                                                    bma_connector)

        self.transactions_service = TransactionsService(self.currency, transactions_processor,
                                                                   dividends_processor,
                                                                   identities_processor, connections_processor,
                                                                   bma_connector)

        self.sources_service = SourcesServices(self.currency, sources_processor,
                                               connections_processor, transactions_processor,
                                               blockchain_processor, bma_connector)

        self.blockchain_service = BlockchainService(self, self.currency, blockchain_processor, connections_processor,
                                                    bma_connector,
                                                    self.identities_service,
                                                    self.transactions_service,
                                                    self.sources_service)

        self.network_service = NetworkService.load(self, self.currency, nodes_processor,
                                                    self.blockchain_service,
                                                    self.identities_service)

    async def remove_connection(self, connection):
        connections_processor = ConnectionsProcessor.instanciate(self)
        connections_processor.remove_connections(connection)

        CertificationsProcessor.instanciate(self).cleanup_connection(connection, connections_processor.pubkeys())
        IdentitiesProcessor.instanciate(self).cleanup_connection(connection)

        SourcesProcessor.instanciate(self).drop_all_of(currency=connection.currency, pubkey=connection.pubkey)

        DividendsProcessor.instanciate(self).cleanup_connection(connection)

        TransactionsProcessor.instanciate(self).cleanup_connection(connection, connections_processor.pubkeys())

        self.db.commit()
        self.connection_removed.emit(connection)

    async def initialize_blockchain(self):
        await asyncio.sleep(2) # Give time for the network to connect to nodes
        await BlockchainProcessor.instanciate(self).initialize_blockchain(self.currency)

    def switch_language(self):
        logging.debug("Loading translations")
        locale = self.parameters.lang
        QLocale.setDefault(QLocale(locale))
        QCoreApplication.removeTranslator(self._translator)
        self._translator = QTranslator(self.qapp)
        if locale == "en":
            QCoreApplication.installTranslator(self._translator)
        elif self._translator.load(":/i18n/{0}".format(locale)):
            if QCoreApplication.installTranslator(self._translator):
                self._logger.debug("Loaded i18n/{0}".format(locale))
            else:
                self._logger.debug("Couldn't load translation")
        else:
            self._logger.debug("Couldn't load i18n/{0}".format(locale))

    def start_coroutines(self):
        self.network_service.start_coroutines()

    async def stop_current_profile(self, closing=False):
        """
        Save the account to the cache
        and stop the coroutines
        """
        await self.network_service.stop_coroutines(closing)
        self.db.commit()

    @asyncify
    async def get_last_version(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
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
        except (aiohttp.ClientError, aiohttp.ServerDisconnectedError, asyncio.TimeoutError, socket.gaierror) as e:
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
