import aiohttp

from duniterpy.documents import BlockUID, BMAEndpoint, Block
from duniterpy.api import bma, errors
from duniterpy.key import SigningKey
from sakia.data.entities import Connection, Identity, Blockchain, Node
from sakia.data.connectors import NodeConnector, BmaConnector
from sakia.data.processors import ConnectionsProcessor, NodesProcessor, BlockchainProcessor, SourcesProcessor
from sakia.gui.component.model import ComponentModel


class ConnectionConfigModel(ComponentModel):
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

    async def create_connection(self, server, port):
        session = aiohttp.ClientSession()
        try:
            self.node_connector = await NodeConnector.from_address(None, server, port, session)
            self.connection = Connection(self.node_connector.node.currency, "", "")
            self.node_connector.node.state = Node.ONLINE
        except:
            session.close()
            raise

    def notification(self):
        return self.app.parameters.notifications

    def set_uid(self, uid):
        self.connection.uid = uid

    def set_scrypt_infos(self, salt, password):
        self.connection.salt = salt
        self.connection.pubkey = SigningKey(self.connection.salt, password).pubkey

    def commit_connection(self):
        ConnectionsProcessor(self.app.db.connections_repo).commit_connection(self.connection)
        NodesProcessor(self.app.db.nodes_repo).commit_node(self.node_connector.node)

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

    async def publish_selfcert(self, salt, password):
        """"
        Publish the self certification of the connection identity
        """
        return await self.identities_processor.publish_selfcert(self.node_connector.node.currency,
                                                         Identity(self.connection.currency,
                                                                  self.connection.pubkey,
                                                                  self.connection.uid),
                                                         salt, password)

    async def check_registered(self):
        """
        Checks for the pubkey and the uid of an account on a given node
        :return: (True if found, local value, network value)
        """
        identity = Identity(self.connection.currency, self.connection.pubkey, self.connection.uid)

        def _parse_uid_certifiers(data):
            return identity.uid == data['uid'], identity.uid, data['uid']

        def _parse_uid_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            for result in data['results']:
                if result["pubkey"] == identity.pubkey:
                    uids = result['uids']
                    for uid_data in uids:
                        if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                            timestamp = uid_data["meta"]["timestamp"]
                            found_uid = uid_data["uid"]
            return identity.uid == found_uid, identity.uid, found_uid

        def _parse_pubkey_certifiers(data):
            return identity.pubkey == data['pubkey'], identity.pubkey, data['pubkey']

        def _parse_pubkey_lookup(data):
            timestamp = BlockUID.empty()
            found_uid = ""
            found_result = ["", ""]
            for result in data['results']:
                uids = result['uids']
                for uid_data in uids:
                    if BlockUID.from_str(uid_data["meta"]["timestamp"]) >= timestamp:
                        timestamp = BlockUID.from_str(uid_data["meta"]["timestamp"])
                        found_uid = uid_data["uid"]
                if found_uid == identity.uid:
                    found_result = result['pubkey'], found_uid
            if found_result[1] == identity.uid:
                return identity.pubkey == found_result[0], identity.pubkey, found_result[0]
            else:
                return False, identity.pubkey, None

        async def execute_requests(parsers, search):
            tries = 0
            request = bma.wot.CertifiersOf
            nonlocal registered
            for endpoint in [e for e in self.node_connector.node.endpoints if isinstance(e, BMAEndpoint)]:
                if not registered[0] and not registered[2]:
                    try:
                        data = await self.node_connector.safe_request(endpoint, request, req_args={'search': search})
                        if data:
                            registered = parsers[request](data)
                        tries += 1
                    except errors.DuniterError as e:
                        if e.ucode in (errors.NO_MEMBER_MATCHING_PUB_OR_UID,
                                       e.ucode == errors.NO_MATCHING_IDENTITY):
                            if request == bma.wot.CertifiersOf:
                                request = bma.wot.Lookup
                                tries = 0
                            else:
                                tries += 1
                        else:
                            tries += 1
                else:
                    break

        # cell 0 contains True if the user is already registered
        # cell 1 contains the uid/pubkey selected locally
        # cell 2 contains the uid/pubkey found on the network
        registered = (False, identity.uid, None)
        # We execute search based on pubkey
        # And look for account UID
        uid_parsers = {
            bma.wot.CertifiersOf: _parse_uid_certifiers,
            bma.wot.Lookup: _parse_uid_lookup
        }
        await execute_requests(uid_parsers, identity.pubkey)

        # If the uid wasn't found when looking for the pubkey
        # We look for the uid and check for the pubkey
        if not registered[0] and not registered[2]:
            pubkey_parsers = {
                bma.wot.CertifiersOf: _parse_pubkey_certifiers,
                bma.wot.Lookup: _parse_pubkey_lookup
            }
            await execute_requests(pubkey_parsers, identity.uid)

        return registered
