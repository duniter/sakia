import logging

from sakia.tools.exceptions import MembershipNotFoundError, LookupFailureError, NoPeerAvailable

from sakia.data.graphs import WoTGraph
from sakia.gui.component.model import ComponentModel


class UserInformationModel(ComponentModel):
    """
    The model of HomeScreen component
    """

    def __init__(self, parent, app, account, community, identity):
        """

        :param sakia.gui.user_information.controller.UserInformationController parent:
        :param sakia.core.Application app: the app
        :param sakia.core.Account account: the account
        :param sakia.core.Community community: the community
        :param sakia.core.registry.Identity identity: the identity
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
        self.identity = identity

    async def identity_timestamps(self):
        """
        Get identity timestamps
        :rtype: tuple
        """
        publish_time = None
        join_date = None
        try:
            identity_selfcert = await self.identity.selfcert(self.community)
            publish_time = await self.community.time(identity_selfcert.timestamp.number)

            join_date = await self.identity.get_join_date(self.community)
        except (MembershipNotFoundError, LookupFailureError, NoPeerAvailable) as e:
            logging.debug(str(e))

        return publish_time, join_date

    async def path_to_identity(self):
        """
        Get the path to a given identity
        :rtype: list[str]
        """
        # calculate path to account member
        graph = WoTGraph(self.app, self.community)
        identities = []
        # if selected member is not the account member...
        if self.identity.pubkey != self.account.pubkey:
            # add path from us to him
            account_identity = await self.account.identity(self.community)
            path = await graph.get_shortest_path_to_identity(self.identity,
                                                             account_identity)
            nodes = graph.nx_graph.nodes(data=True)
            if path:
                for node_id in path:
                    node = [n for n in nodes if n[0] == node_id][0]
                    identities.append(node[1]['text'])
        return identities

    async def search_identity(self, pubkey):
        """
        Set the identity starting by a pubkey
        :param str pubkey:
        """
        self.identity = await self.app.identities_registry.future_find(pubkey, self.community)
