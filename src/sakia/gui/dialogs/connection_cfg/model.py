import aiohttp
from PyQt5.QtCore import QObject
from duniterpy.key import SigningKey
from sakia.data.entities import Connection
from sakia.data.processors import ConnectionsProcessor, BlockchainProcessor, \
    SourcesProcessor, TransactionsProcessor, DividendsProcessor, IdentitiesProcessor


class ConnectionConfigModel(QObject):
    """
    The model of AccountConfig component
    """

    def __init__(self, parent, app, connection, identities_processor, node_connector=None):
        """

        :param sakia.gui.dialogs.account_cfg.controller.AccountConfigController parent:
        :param sakia.app.Application app: the main application
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor
        :param sakia.data.connectors.NodeConnector node_connector: the node connector
        """
        super().__init__(parent)
        self.app = app
        self.connection = connection
        self.identities_processor = identities_processor

    async def create_connection(self):
        self.connection = Connection(self.app.currency, "", "")

    def notification(self):
        return self.app.parameters.notifications

    def set_uid(self, uid):
        self.connection.uid = uid

    def set_scrypt_infos(self, salt, password, scrypt_params):
        self.connection.salt = salt
        self.connection.scrypt_N = scrypt_params.N
        self.connection.scrypt_r = scrypt_params.r
        self.connection.scrypt_p = scrypt_params.p
        self.connection.password = password
        self.connection.pubkey = SigningKey(self.connection.salt, password, scrypt_params).pubkey

    def set_pubkey(self, pubkey, scrypt_params):
        self.connection.salt = ""
        self.connection.scrypt_N = scrypt_params.N
        self.connection.scrypt_r = scrypt_params.r
        self.connection.scrypt_p = scrypt_params.p
        self.connection.password = ""
        self.connection.pubkey = pubkey

    def insert_or_update_connection(self):
        ConnectionsProcessor(self.app.db.connections_repo).commit_connection(self.connection)

    def insert_or_update_identity(self, identity):
        self.identities_processor.insert_or_update_identity(identity)

    def generate_revocation(self):
        return self.app.documents_service.generate_revocation(self.connection,
                                                              self.connection.salt,
                                                              self.connection.password)

    def generate_identity(self):
        return self.app.documents_service.generate_identity(self.connection)

    async def initialize_blockchain(self, log_stream):
        """
        Download blockchain information locally
        :param function log_stream: a method to log data in the screen
        :return:
        """
        blockchain_processor = BlockchainProcessor.instanciate(self.app)
        await blockchain_processor.initialize_blockchain(self.app.currency)

    async def initialize_sources(self, transactions, dividends, log_stream, progress):
        """
        Download sources information locally
        :param function log_stream: a method to log data in the screen
        :param function progress: a callback to display progress
        :return:
        """
        log_stream("Parsing sources...")
        await self.app.sources_service.refresh_sources_of_pubkey(self.connection.pubkey, transactions, dividends,
                                                                 None, log_stream, progress)
        log_stream("Sources parsed succefully !")

    async def initialize_identity(self, identity, log_stream, progress):
        """
        Download identity information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param function log_stream: a method to log data in the screen
        :return:
        """
        await self.identities_processor.initialize_identity(identity, log_stream, progress)

    async def initialize_certifications(self, identity, log_stream, progress):
        """
        Download certifications information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param function log_stream: a method to log data in the screen
        :return:
        """
        await self.app.identities_service.initialize_certifications(identity, log_stream, progress)

    async def initialize_transactions(self, identity, log_stream, progress):
        """
        Download certifications information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param function log_stream: a method to log data in the screen
        :return:
        """
        transactions_processor = TransactionsProcessor.instanciate(self.app)
        return await transactions_processor.initialize_transactions(identity, log_stream, progress)

    async def initialize_dividends(self, identity, transactions, log_stream, progress):
        """
        Download certifications information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx processor
        :param function log_stream: a method to log data in the screen
        :return:
        """
        dividends_processor = DividendsProcessor.instanciate(self.app)
        return await dividends_processor.initialize_dividends(identity, transactions, log_stream, progress)

    async def publish_selfcert(self, identity):
        """"
        Publish the self certification of the connection identity
        """
        result = await self.app.documents_service.broadcast_identity(self.connection, identity.document())
        return result

    async def check_registered(self):
        identities_processor = IdentitiesProcessor.instanciate(self.app)
        return await identities_processor.check_registered(self.connection)

    def key_exists(self):
        return self.connection.pubkey in ConnectionsProcessor.instanciate(self.app).pubkeys()

    def blockchain_parameters(self):
        blockchain_processor = BlockchainProcessor.instanciate(self.app)
        return blockchain_processor.parameters(self.app.currency)
