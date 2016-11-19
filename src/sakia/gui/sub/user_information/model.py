import logging

from sakia.errors import NoPeerAvailable

from sakia.gui.component.model import ComponentModel


class UserInformationModel(ComponentModel):
    """
    The model of HomeScreen component
    """

    def __init__(self, parent, app, currency, identity, identities_service):
        """

        :param sakia.gui.user_information.controller.UserInformationController parent:
        :param sakia.core.Application app: the app
        :param str currency: the currency currently requested
        :param sakia.data.entities.Identity identity: the identity
        :param sakia.services.IdentitiesService identities_service: the identities service of current currency
        """
        super().__init__(parent)
        self.app = app
        self.currency = currency
        self.identity = identity
        self.identities_service = identities_service

    async def load_identity(self):
        """
        Ask network service to request identity informations
        """
        await self.identities_service.load_memberships(self.identity)
        await self.identities_service.load_certifiers_of(self.identity)
        await self.identities_service.load_certified_by(self.identity)
