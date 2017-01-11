import aiohttp
from PyQt5.QtCore import QObject
from duniterpy.documents import BlockUID, BMAEndpoint
from duniterpy.api import bma, errors
from duniterpy.key import SigningKey
from sakia.data.entities import Connection, Identity, Node
from sakia.data.connectors import NodeConnector
from sakia.data.processors import ConnectionsProcessor, NodesProcessor, BlockchainProcessor, \
    SourcesProcessor, CertificationsProcessor, TransactionsProcessor, DividendsProcessor


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
        self.node_connector = node_connector
        self.identities_processor = identities_processor

    async def create_connection(self, server, port, secured):
        node_connector = await NodeConnector.from_address(None, secured, server, port,
                                                               user_parameters=self.app.parameters)
        currencies = self.app.db.connections_repo.get_currencies()
        if len(currencies) > 0 and node_connector.node.currency != currencies[0]:
            raise ValueError("""This node is running for {0} network.<br/>
Current database is storing {1} network.""".format(node_connector.node.currency, currencies[0]))
        self.node_connector = node_connector
        self.connection = Connection(self.node_connector.node.currency, "", "")
        self.node_connector.node.state = Node.ONLINE

    def notification(self):
        return self.app.parameters.notifications

    def set_uid(self, uid):
        self.connection.uid = uid

    def set_scrypt_infos(self, salt, password, scrypt_params):
        self.connection.salt = salt
        self.connection.N = scrypt_params.N
        self.connection.r = scrypt_params.r
        self.connection.p = scrypt_params.p
        self.connection.password = password
        self.connection.pubkey = SigningKey(self.connection.salt, password, scrypt_params).pubkey

    def insert_or_update_connection(self):
        ConnectionsProcessor(self.app.db.connections_repo).commit_connection(self.connection)
        NodesProcessor(self.app.db.nodes_repo).commit_node(self.node_connector.node)

    def insert_or_update_identity(self, identity):
        self.identities_processor.insert_or_update_identity(identity)

    async def initialize_blockchain(self, log_stream):
        """
        Download blockchain information locally
        :param function log_stream: a method to log data in the screen
        :return:
        """
        blockchain_processor = BlockchainProcessor.instanciate(self.app)
        await blockchain_processor.initialize_blockchain(self.node_connector.node.currency, log_stream)

    async def initialize_sources(self, log_stream):
        """
        Download sources information locally
        :param function log_stream: a method to log data in the screen
        :return:
        """
        sources_processor = SourcesProcessor.instanciate(self.app)
        await sources_processor.initialize_sources(self.node_connector.node.currency, self.connection.pubkey, log_stream)

    async def initialize_identity(self, identity, log_stream):
        """
        Download identity information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param function log_stream: a method to log data in the screen
        :return:
        """
        await self.identities_processor.initialize_identity(identity, log_stream)

    async def initialize_certifications(self, identity, log_stream):
        """
        Download certifications information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param function log_stream: a method to log data in the screen
        :return:
        """
        certifications_processor = CertificationsProcessor.instanciate(self.app)
        await certifications_processor.initialize_certifications(identity, log_stream)

    async def initialize_transactions(self, identity, log_stream):
        """
        Download certifications information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param function log_stream: a method to log data in the screen
        :return:
        """
        transactions_processor = TransactionsProcessor.instanciate(self.app)
        return await transactions_processor.initialize_transactions(identity, log_stream)

    async def initialize_dividends(self, identity, transactions, log_stream):
        """
        Download certifications information locally
        :param sakia.data.entities.Identity identity: the identity to initialize
        :param List[sakia.data.entities.Transaction] transactions: the list of transactions found by tx processor
        :param function log_stream: a method to log data in the screen
        :return:
        """
        dividends_processor = DividendsProcessor.instanciate(self.app)
        return await dividends_processor.initialize_dividends(identity, transactions, log_stream)

    async def publish_selfcert(self):
        """"
        Publish the self certification of the connection identity
        """
        return await self.app.documents_service.broadcast_identity(self.connection, self.connection.password)

    async def check_registered(self):
        """
        Checks for the pubkey and the uid of an account on a given node
        :return: (True if found, local value, network value)
        """
        identity = Identity(self.connection.currency, self.connection.pubkey, self.connection.uid)
        found_identity = Identity(self.connection.currency, self.connection.pubkey, self.connection.uid)

        def _parse_uid_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            for result in data['results']:
                if result["pubkey"] == identity.pubkey:
                    uids = result['uids']
                    for uid_data in uids:
                        if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                            timestamp = BlockUID.from_str(uid_data["meta"]["timestamp"])
                            found_identity.blockstamp = timestamp
                            found_uid = uid_data["uid"]
                            found_identity.signature = uid_data["self"]
            return identity.uid == found_uid, identity.uid, found_uid

        def _parse_pubkey_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            found_result = ["", ""]
            for result in data['results']:
                uids = result['uids']
                for uid_data in uids:
                    if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                        timestamp = BlockUID.from_str(uid_data["meta"]["timestamp"])
                        found_identity.blockstamp = timestamp
                        found_uid = uid_data["uid"]
                        found_identity.signature = uid_data["self"]
                if found_uid == identity.uid:
                    found_result = result['pubkey'], found_uid
            if found_result[1] == identity.uid:
                return identity.pubkey == found_result[0], identity.pubkey, found_result[0]
            else:
                return False, identity.pubkey, None

        async def execute_requests(parser, search):
            tries = 0
            nonlocal registered
            for endpoint in [e for e in self.node_connector.node.endpoints if isinstance(e, BMAEndpoint)]:
                if not registered[0] and not registered[2]:
                    try:
                        data = await self.node_connector.safe_request(endpoint, bma.wot.lookup,
                                                                      req_args={'search': search},
                                                                      proxy=self.app.parameters.proxy())
                        if data:
                            registered = parser(data)
                        tries += 1
                    except errors.DuniterError as e:
                        if e.ucode in (errors.NO_MEMBER_MATCHING_PUB_OR_UID, errors.NO_MATCHING_IDENTITY):
                                tries += 1
                        else:
                            raise
                else:
                    break

        # cell 0 contains True if the user is already registered
        # cell 1 contains the uid/pubkey selected locally
        # cell 2 contains the uid/pubkey found on the network
        registered = (False, identity.uid, None)
        # We execute search based on pubkey
        # And look for account UID
        await execute_requests(_parse_uid_lookup, identity.pubkey)

        # If the uid wasn't found when looking for the pubkey
        # We look for the uid and check for the pubkey
        if not registered[0] and not registered[2]:
            await execute_requests(_parse_pubkey_lookup, identity.uid)

        return registered, found_identity

