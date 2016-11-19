import logging
import asyncio
import networkx
from .base_graph import BaseGraph
from .constants import NodeStatus


class WoTGraph(BaseGraph):
    def __init__(self, app, blockchain_service, identities_service, nx_graph=None):
        """
        Init WoTGraph instance
        :param sakia.app.Application app: the app
        :param sakia.data.entities.Connection connection: the connection
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        :param networkx.Graph nx_graph: The networkx graph
        :return:
        """
        super().__init__(app, blockchain_service, identities_service, nx_graph)

    async def initialize(self, center_identity, connection_identity):
        node_status = await self.node_status(center_identity, connection_identity)

        self.add_identity(center_identity, node_status)

        # create Identity from node metadata
        certifier_coro = asyncio.ensure_future(self.identities_service.load_certifiers_of(center_identity))
        certified_coro = asyncio.ensure_future(self.identities_service.load_certified_by(center_identity))

        await asyncio.gather(certifier_coro, certified_coro)

        # populate graph with certifiers-of
        certifier_list = self.identities_service.certifications_received(center_identity.pubkey)
        certifier_coro = asyncio.ensure_future(self.add_certifier_list(certifier_list,
                                                                       center_identity, connection_identity))
        # populate graph with certified-by
        certified_list = self.identities_service.certifications_sent(center_identity.pubkey)
        certified_coro = asyncio.ensure_future(self.add_certified_list(certified_list,
                                                                       center_identity, connection_identity))

        await asyncio.gather(certifier_coro, certified_coro)

    async def get_shortest_path_to_identity(self, from_identity, to_identity):
        """
        Return path list of nodes from from_identity to to_identity
        :param identity from_identity:
        :param identity to_identity:
        :return:
        """
        path = list()

        logging.debug("path between %s to %s..." % (from_identity.uid, to_identity.uid))
        self.add_identity(from_identity, NodeStatus.HIGHLIGHTED)

        # recursively feed graph searching for account node...
        await self.explore_to_find_member(from_identity, to_identity)

        # calculate path of nodes between identity and to_identity
        try:
            path = networkx.shortest_path(self.nx_graph, from_identity.pubkey, to_identity.pubkey)
        except networkx.exception.NetworkXException as e:
            logging.debug(str(e))

        return path

    async def explore_to_find_member(self, from_identity, to_identity):
        """
        Scan graph to find identity
        :param sakia.data.entities.Identity from_identity: Scan starting point
        :param sakia.data.entities.Identity to_identity: Scan goal
        """
        explored = []
        explorable = [from_identity]

        while len(explorable) > 0:
            current = explorable.pop()
            certified_list = await self.identities_service.certifications_sent(current.pubkey)

            await self.add_certified_list(certified_list, current, from_identity)
            if to_identity.pubkey in [data['identity'].pubkey for data in certified_list]:
                return True

            explored.append(current)
            for entry in certified_list:
                if entry['identity'] not in explored + explorable:
                    explorable.append(entry['identity'])

        return False
