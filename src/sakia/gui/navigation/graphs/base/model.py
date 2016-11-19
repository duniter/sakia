from sakia.gui.component.model import ComponentModel


class BaseGraphModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, account, community):
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community

    async def get_identity(self, pubkey):
        """
        Get identity from pubkey
        :param str pubkey: Identity pubkey
        :rtype: sakia.core.registry.Identity
        """
        return await self.app.identities_registry.future_find(pubkey, self.community)
