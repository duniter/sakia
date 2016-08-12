from ..base.model import BaseGraphModel
from sakia.core.graph import ExplorerGraph
from sakia.tools.exceptions import NoPeerAvailable


class ExplorerModel(BaseGraphModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, account, community):
        super().__init__(parent, app, account, community)
        self.app = app
        self.account = account
        self.community = community
        self.explorer_graph = ExplorerGraph(self.app, self.community)
        self.identity = None

    @property
    def graph(self):
        """
        Return underlying graph object
        """
        return self.explorer_graph

    async def set_identity(self, identity):
        """
        Change current identity
        If identity is None, it defaults to account identity
        :param sakia.core.registry.Identity identity: the new identity to show
        :return:
        """
        if identity:
            self.identity = identity
        else:
            identity_account = await self.account.identity(self.community)
            self.identity = identity_account

    async def start_exploration(self, steps):
        """
        Get nx graph of current identity wot graph
        :rtype: sakia.core.registry.Identity
        """
        return self.explorer_graph.start_exploration(self.identity, steps)

    async def maximum_steps(self):
        """
        Get the maximum steps to display in the view
        """
        try:
            parameters = await self.community.parameters()
            return parameters['stepMax']
        except NoPeerAvailable:
            return 0
