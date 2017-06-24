from sakia.data.graphs import WoTGraph
from ..base.model import BaseGraphModel
from sakia.data.processors import ConnectionsProcessor


class WotModel(BaseGraphModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, blockchain_service, identities_service):
        """
        Constructor of a model of WoT component

        :param sakia.gui.identities.controller.IdentitiesController parent: the controller
        :param sakia.app.Application app: the app
        :param sakia.services.BlockchainService blockchain_service: the blockchain service
        :param sakia.services.IdentitiesService identities_service: the identities service
        """
        super().__init__(parent, app, blockchain_service, identities_service)
        self.app = app
        self._connections_processor = ConnectionsProcessor.instanciate(self.app)
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service
        self.wot_graph = WoTGraph(self.app, self.blockchain_service, self.identities_service)
        self.identity = None

    async def set_identity(self, identity=None):
        """
        Change current identity
        If identity is None, it defaults to account identity
        :param sakia.core.registry.Identity identity: the new identity to show
        :return:
        """
        for pubkey in self._connections_processor.pubkeys():
            if identity:
                if identity.pubkey == pubkey:
                    self.identity = identity
                    self.wot_graph.offline_init(identity)
                    break
            else:
                connection_identity = self.identities_service.get_identity(pubkey)
                if connection_identity:
                    self.identity = connection_identity
                    self.wot_graph.offline_init(connection_identity)
                    break
        else:
            # create empty graph instance
            if identity:
                self.identity = identity
                await self.wot_graph.initialize(self.identity)

    def refresh(self, identity):
        if self.identity == identity:
            # create empty graph instance
            self.wot_graph.offline_init(identity)
            return True
        return False

    def get_nx_graph(self):
        """
        Get nx graph of current identity wot graph
        :rtype: sakia.core.registry.Identity
        """
        return self.wot_graph.nx_graph
