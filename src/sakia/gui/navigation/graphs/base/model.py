from PyQt5.QtCore import QObject

class BaseGraphModel(QObject):
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
        super().__init__(parent)
        self.app = app
        self.blockchain_service = blockchain_service
        self.identities_service = identities_service

    def get_identity(self, pubkey):
        """
        Get identity from pubkey
        :param str pubkey: Identity pubkey
        :rtype: sakia.core.registry.Identity
        """
        return self.identities_service.get_identity(pubkey, self.app.currency)
