from sakia.gui.component.model import ComponentModel
from duniterpy.api import errors, bma
from sakia.errors import NoPeerAvailable

import logging


class SearchUserModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, currency, identities_processor):
        """

        :param sakia.gui.search_user.controller.NetworkController parent: the controller
        :param sakia.core.Application app: the app
        :param str currency: the currency
        :param sakia.data.processors.IdentitiesProcessor identities_processor: the identities processor
        """
        super().__init__(parent)
        self.app = app
        self.currency = currency
        self.identities_processor = identities_processor
        self._nodes = list()
        self._current_identity = None

    def identity(self):
        """
        Get current identity selected
        :rtype: sakia.core.registry.Identity
        """
        return self._current_identity

    def user_nodes(self):
        """
        Gets user nodes
        :return:
        """
        return [n.uid for n in self._nodes]

    async def find_user(self, text):
        """
        Search for a user
        :param text:
        :return:
        """
        try:
            self._nodes = await self.identities_processor.lookup(self.currency, text)
        except errors.DuniterError as e:
            if e.ucode == errors.NO_MATCHING_IDENTITY:
                self._nodes = list()
            else:
                logging.debug(str(e))
        except NoPeerAvailable as e:
            logging.debug(str(e))

    def select_identity(self, index):
        """
        Select an identity from a node index
        :param index:
        :return:
        """
        if index < 0 or index >= len(self._nodes):
            self._current_identity = None
            return False
        self._current_identity = self._nodes[index]