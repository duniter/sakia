from sakia.data.graphs import WoTGraph
from ..base.model import BaseGraphModel


class WotModel(BaseGraphModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, account, community):
        super().__init__(parent, app, account, community)
        self.app = app
        self.account = account
        self.community = community
        self.wot_graph = WoTGraph(self.app, self.community)
        self.identity = None

    async def set_identity(self, identity=None):
        """
        Change current identity
        If identity is None, it defaults to account identity
        :param sakia.core.registry.Identity identity: the new identity to show
        :return:
        """
        identity_account = await self.account.identity(self.community)
        if identity:
            self.identity = identity
        else:
            self.identity = identity_account

        # create empty graph instance
        await self.wot_graph.initialize(self.identity, identity_account)

    async def get_nx_graph(self):
        """
        Get nx graph of current identity wot graph
        :rtype: sakia.core.registry.Identity
        """
        return self.wot_graph.nx_graph

    async def get_shortest_path(self):
        """
        Get shortest path between current identity and account
        :rtype: list[str]
        """
        identity_account = await self.account.identity(self.community)
        # if selected member is not the account member...
        if self.identity.pubkey != identity_account.pubkey:
            path = await self.wot_graph.get_shortest_path_to_identity(self.identity, identity_account)
            return path
        return []
