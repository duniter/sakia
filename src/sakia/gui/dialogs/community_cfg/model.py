from sakia.gui.component.model import ComponentModel
from sakia.data.entities import Node
from sakia.data.connectors import NodeConnector
import aiohttp
from sakia.models.peering import PeeringTreeModel


class CommunityConfigModel(ComponentModel):
    """
    The model of CommunityConfig component
    """

    def __init__(self, parent, app, user_parameters, currency, identity, nodes_processor, identities_processor):
        """

        :param sakia.gui.dialogs.Community_cfg.controller.CommunityConfigController parent:
        :param sakia.core.Application app:
        :param sakia.data.entities.UserParameters user_parameters: the parameters of the current profile
        :param str currency: the currency configured
        :param sakia.data.entities.Identity identity: the identity
        :param sakia.data.processors.NodesProcessor nodes_processor: the nodes processor
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor
        """
        super().__init__(parent)
        self.app = app
        self.nodes_tree_model = None
        self.nodes = []
        self.user_parameters = user_parameters
        self.currency = currency
        self.identity = identity
        self.nodes_processor = nodes_processor
        self.identities_processor = identities_processor

    async def create_community(self, server, port):
        with aiohttp.ClientSession() as session:
            node_connector = await NodeConnector.from_address(None, server, port, session)
            self.nodes.append(node_connector.node)

    async def add_node(self, server, port):
        with aiohttp.ClientSession() as session:
            node_connector = await NodeConnector.from_address(None, server, port, session)
            self.nodes.append(node_connector.node)
        self.nodes_tree_model.refresh_tree()

    def remove_node(self, index):
        self.nodes.remove(index)
        self.nodes_tree_model.refresh_tree()

    async def check_registered(self):
        return await self.identities_processor.check_registered(self.currency, self.identity)

    #async def publish_selfcert(self, password):
    #    return await self.account.send_selfcert(password, self.community)

    def init_nodes_model(self):
        # We add already known peers to the displayed list
        self.nodes_tree_model = PeeringTreeModel(self.nodes)

    def notification(self):
        self.user_parameters.notifications
