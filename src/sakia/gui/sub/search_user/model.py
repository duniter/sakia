from PyQt5.QtCore import QObject
from duniterpy.api import errors
from sakia.errors import NoPeerAvailable
from sakia.data.processors import IdentitiesProcessor, ContactsProcessor

import logging


class SearchUserModel(QObject):
    """
    The model of Navigation component
    """

    def __init__(self, parent, app):
        """

        :param sakia.gui.search_user.controller.NetworkController parent: the controller
        :param sakia.app.Application app: the app
        """
        super().__init__(parent)
        self.app = app
        self.identities_processor = IdentitiesProcessor.instanciate(app)
        self.contacts_processor = ContactsProcessor.instanciate(app)
        self._nodes = list()
        self._current_identity = None

    def contacts(self):
        return self.contacts_processor.contacts()

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
            self._nodes = await self.identities_processor.lookup(self.app.currency, text)
        except errors.DuniterError as e:
            if e.ucode == errors.NO_MATCHING_IDENTITY:
                self._nodes = list()
            else:
                logging.debug(str(e))
        except NoPeerAvailable as e:
            logging.debug(str(e))
        except BaseException as e:
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
        return True

    def clear(self):
        self._current_identity = None
        self._nodes = list()