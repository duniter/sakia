import logging

from PyQt5.QtGui import QCursor
from PyQt5.QtCore import QObject, pyqtSignal
from sakia.errors import NoPeerAvailable

from duniterpy.api import errors
from sakia.data.entities import Identity
from sakia.decorators import once_at_a_time, asyncify
from sakia.gui.widgets.context_menu import ContextMenu
from .model import IdentitiesModel
from .view import IdentitiesView


class IdentitiesController(QObject):
    """
    The navigation panel
    """
    view_in_wot = pyqtSignal(Identity)

    def __init__(self, parent, view, model, password_asker=None):
        """
        Constructor of the navigation component

        :param sakia.gui.identities.view.IdentitiesView view: the view
        :param sakia.gui.identities.model.IdentitiesModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self.password_asker = password_asker
        self.view.search_by_text_requested.connect(self.search_text)
        self.view.search_directly_connected_requested.connect(self.search_direct_connections)
        self.view.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        table_model = self.model.init_table_model()
        self.view.set_table_identities_model(table_model)

    @classmethod
    def create(cls, parent, app, blockchain_service, identities_service):
        view = IdentitiesView(parent.view)
        model = IdentitiesModel(None, app, blockchain_service, identities_service)
        identities = cls(parent, view, model)
        model.setParent(identities)
        identities.view_in_wot.connect(app.view_in_wot)
        return identities

    def identity_context_menu(self, point):
        index = self.view.table_identities.indexAt(point)
        valid, identities = self.model.table_data(index)
        if valid:
            menu = ContextMenu.from_data(self.view, self.model.app, None, (identities,))
            menu.view_identity_in_wot.connect(self.view_in_wot)
            menu.identity_information_loaded.connect(self.model.table_model.sourceModel().identity_loaded)

            # Show the context menu.
            menu.qmenu.popup(QCursor.pos())

    @once_at_a_time
    @asyncify
    async def search_text(self, text):
        """
        Search identities using given text
        :param str text: text to search
        :return:
        """
        try:
            identities = await self.model.lookup_identities(text)
            self.model.refresh_identities(identities)
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                logging.debug(str(e))
        except NoPeerAvailable as e:
            logging.debug(str(e))

    def search_direct_connections(self):
        """
        Search identities directly connected to account
        :return:
        """
        identities = self.model.linked_identities()
        self.model.refresh_identities(identities)
