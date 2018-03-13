import asyncio
import networkx
from .base_graph import BaseGraph


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

    async def initialize(self, center_identity):
        self.nx_graph.clear()
        node_status = self.node_status(center_identity)

        self.add_identity(center_identity, node_status)

        # create Identity from node metadata
        certifier_coro = self.identities_service.load_certifiers_of(center_identity)
        certified_coro = self.identities_service.load_certified_by(center_identity)

        certifier_list, certified_list = await asyncio.gather(*[certifier_coro, certified_coro])

        certifier_list, certified_list = await self.identities_service.load_certs_in_lookup(center_identity,
                                                                                            certifier_list,
                                                                                            certified_list)

        # populate graph with certifiers-of
        self.add_certifier_list(certifier_list, center_identity)
        # populate graph with certified-by
        self.add_certified_list(certified_list, center_identity)

    def offline_init(self, center_identity):
        node_status = self.node_status(center_identity)

        self.add_identity(center_identity, node_status)

        # populate graph with certifiers-of
        certifier_list = self.identities_service.certifications_received(center_identity.pubkey)
        certifier_list = {c: self.identities_service.get_identity(c.certifier) for c in certifier_list}
        self.add_certifier_list(certifier_list, center_identity)
        # populate graph with certified-by
        certified_list = self.identities_service.certifications_sent(center_identity.pubkey)
        certified_list = {c: self.identities_service.get_identity(c.certified) for c in certified_list}
        self.add_certified_list(certified_list, center_identity)
