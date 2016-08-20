from sakia.gui.component.model import ComponentModel
from sakia.core.net import Node
from sakia.core import Community
import aiohttp
from sakia.models.peering import PeeringTreeModel


class CommunityConfigModel(ComponentModel):
    """
    The model of CommunityConfig component
    """

    def __init__(self, parent, app, account, community):
        """

        :param sakia.gui.dialogs.Community_cfg.controller.CommunityConfigController parent:
        :param sakia.core.Application app:
        :param sakia.core.Account account:
        :param sakia.core.Community community:
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
        self.nodes = []
        self.nodes_tree_model = None

    async def create_community(self, server, port):
        node = await Node.from_address(None, server, port, session=aiohttp.ClientSession())
        self.community = Community.create(node)

    async def add_node(self, server, port):
        node = await Node.from_address(self.community.currency, server, port, session=self.community.network.session)
        self.community.add_node(node)
        self.nodes_tree_model.refresh_tree()

    def remove_node(self, index):
        self.community.remove_node(index)
        self.nodes_tree_model.refresh_tree()

    async def check_registered(self):
        return await self.account.check_registered(self.community)

    async def publish_selfcert(self, password):
        return await self.account.send_selfcert(password, self.community)

    def init_nodes_model(self):
        # We add already known peers to the displayed list
        self.nodes = self.community.network.root_nodes
        self.nodes_tree_model = PeeringTreeModel(self.community)

    def notification(self):
        self.app.preferences['notifications']

