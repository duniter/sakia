from sakia.gui.component.controller import ComponentController
from .model import IdentitiesModel
from .view import IdentitiesView
from sakia.tools.decorators import once_at_a_time, asyncify
from sakia.gui.widgets.context_menu import ContextMenu
from PyQt5.QtGui import QCursor
from sakia.core.registry import Identity, BlockchainState
from duniterpy.documents.block import BlockUID
from duniterpy.api import bma, errors
from sakia.tools.exceptions import NoPeerAvailable
import logging


class IdentitiesController(ComponentController):
    """
    The navigation panel
    """

    def __init__(self, parent, view, model, password_asker=None):
        """
        Constructor of the navigation component

        :param sakia.gui.identities.view.IdentitiesView view: the view
        :param sakia.gui.identities.model.IdentitiesModel model: the model
        """
        super().__init__(parent, view, model)
        self.password_asker = password_asker
        self.view.search_by_text_requested.connect(self.search_text)
        self.view.search_directly_connected_requested.connect(self.search_direct_connections)
        self.view.table_identities.customContextMenuRequested.connect(self.identity_context_menu)
        table_model = self.model.init_table_model()
        self.view.set_table_identities_model(table_model)

    @property
    def view(self) -> IdentitiesView:
        return self._view

    @property
    def model(self) -> IdentitiesModel:
        return self._model

    @property
    def app(self):
        return self.model.app

    @property
    def community(self):
        return self.model.community

    @property
    def account(self):
        return self.model.account

    @classmethod
    def create(cls, parent, app, **kwargs):
        account = kwargs['account']
        community = kwargs['community']

        view = IdentitiesView(parent.view)
        model = IdentitiesModel(None, app, account, community)
        txhistory = cls(parent, view, model)
        model.setParent(txhistory)
        return txhistory

    @once_at_a_time
    @asyncify
    async def identity_context_menu(self, point):
        index = self.view.table_identities.indexAt(point)
        valid, identity = await self.model.table_data(index)
        if valid:
            menu = ContextMenu.from_data(self.view, self.app, self.account, self.community, self.password_asker,
                                         (identity,))
            menu.view_identity_in_wot.connect(self.view_in_wot)

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
            response = await self.community.bma_access.future_request(bma.wot.Lookup, {'search': text})
            identities = []
            for identity_data in response['results']:
                for uid_data in identity_data['uids']:
                    identity = Identity.from_handled_data(uid_data['uid'],
                                                          identity_data['pubkey'],
                                                          BlockUID.from_str(uid_data['meta']['timestamp']),
                                                          BlockchainState.BUFFERED)
                    identities.append(identity)
            await self.model.refresh_identities(identities)
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                logging.debug(str(e))
        except NoPeerAvailable as e:
            logging.debug(str(e))

    @once_at_a_time
    @asyncify
    async def search_direct_connections(self):
        """
        Search identities directly connected to account
        :return:
        """
        self_identity = await self.account.identity(self.community)
        account_connections = []
        certs_of = await self_identity.unique_valid_certifiers_of(self.app.identities_registry, self.community)
        for p in certs_of:
            account_connections.append(p['identity'])
        certifiers_of = [p for p in account_connections]
        certs_by = await self_identity.unique_valid_certified_by(self.app.identities_registry, self.community)
        for p in certs_by:
            account_connections.append(p['identity'])
        certified_by = [p for p in account_connections
                        if p.pubkey not in [i.pubkey for i in certifiers_of]]
        identities = certifiers_of + certified_by
        await self.model.refresh_identities(identities)
