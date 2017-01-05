from PyQt5.QtCore import QObject
from sakia.data.processors import CertificationsProcessor, BlockchainProcessor


class UserInformationModel(QObject):
    """
    The model of HomeScreen component
    """

    def __init__(self, parent, app, currency, identity):
        """

        :param sakia.gui.user_information.controller.UserInformationController parent:
        :param sakia.core.Application app: the app
        :param str currency: the currency currently requested
        :param sakia.data.entities.Identity identity: the identity
        :param sakia.services.IdentitiesService identities_service: the identities service of current currency
        """
        super().__init__(parent)
        self._certifications_processor = CertificationsProcessor.instanciate(app)
        self._blockchain_processor = BlockchainProcessor.instanciate(app)
        self.app = app
        self.currency = currency
        self.identity = identity
        if identity:
            self.certs_sent = self._certifications_processor.certifications_sent(currency, identity.pubkey)
            self.certs_received = self._certifications_processor.certifications_received(currency, identity.pubkey)
        if currency:
            self.identities_service = self.app.identities_services[self.currency]
        else:
            self.identities_service = None

    async def load_identity(self, identity):
        """
        Ask network service to request identity informations
        """
        self.identity = identity
        self.identity = await self.identities_service.load_memberships(self.identity)
        self.identity = await self.identities_service.load_requirements(self.identity)

    def set_currency(self, currency):
        self.currency = currency
        self.identities_service = self.app.identities_services[self.currency]

    async def nb_certs(self):
        certs = await self.identities_service.load_certifiers_of(self.identity)
        return len(certs)

    def mstime_remaining(self):
        return self.identities_service.expiration_date(self.identity) \
               - self._blockchain_processor.time(self.identity.currency)

    def outdistanced(self):
        return self.identity_is_outdistanced