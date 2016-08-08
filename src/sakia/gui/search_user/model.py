from sakia.core.registry import BlockchainState
from ..component.model import ComponentModel
from duniterpy.api import errors, bma
from sakia.tools.exceptions import NoPeerAvailable

import logging


class SearchUserModel(ComponentModel):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app, account, community):
        """

        :param sakia.gui.search_user.controller.NetworkController parent: the controller
        :param sakia.core.Application app: the app
        :param sakia.core.Account account: the account
        :param sakia.core.Community community: the community
        """
        super().__init__(parent)
        self.app = app
        self.account = account
        self.community = community
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
        return [n['uid'] for n in self._nodes]

    async def find_user(self, text):
        """
        Search for a user
        :param text:
        :return:
        """
        try:
            response = await self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})

            nodes = {}
            for identity in response['results']:
                nodes[identity['pubkey']] = identity['uids'][0]['uid']

            if nodes:
                self._nodes = list()
                for pubkey, uid in nodes.items():
                    self._nodes.append({'pubkey': pubkey, 'uid': uid})
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
        node = self._nodes[index]
        metadata = {'id': node['pubkey'], 'text': node['uid']}
        self._current_identity = self.app.identities_registry.from_handled_data(
                metadata['text'],
                metadata['id'],
                None,
                BlockchainState.VALIDATED,
                self.community
            )