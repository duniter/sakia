import logging

from PyQt5.QtCore import QObject
from sakia.errors import NoPeerAvailable

from duniterpy.api import errors
from sakia.decorators import asyncify
from .model import InformationsModel
from .view import InformationsView


class InformationsController(QObject):
    """
    The informations component
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the informations component

        :param sakia.gui.informations.view.InformationsView view: the view
        :param sakia.gui.informations.model.InformationsModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self._logger = logging.getLogger('sakia')

    @property
    def informations_view(self):
        """
        :rtype: sakia.gui.informations.view.InformationsView
        """
        return self.view

    @classmethod
    def create(cls, parent, app, connection, blockchain_service, identities_service, sources_service):
        """

        :param parent:
        :param sakia.app.Application app:
        :param connection:
        :param blockchain_service:
        :param identities_service:
        :param sources_service:
        :return:
        """
        view = InformationsView(parent.view)
        model = InformationsModel(None, app, connection, blockchain_service, identities_service, sources_service)
        informations = cls(parent, view, model)
        model.setParent(informations)
        informations.init_view_text()
        app.identity_changed.connect(informations.handle_identity_change)
        app.new_transfer.connect(informations.refresh_localized_data)
        app.new_dividend.connect(informations.refresh_localized_data)
        app.referential_changed.connect(informations.refresh_localized_data)
        app.sources_refreshed.connect(informations.refresh_localized_data)
        return informations

    @asyncify
    async def init_view_text(self):
        """
        Initialization of text in informations view
        """
        referentials = self.model.referentials()
        self.view.set_rules_text_no_dividend()
        self.view.set_general_text_no_dividend()
        self.view.set_text_referentials(referentials)
        params = self.model.parameters()
        if params:
            self.view.set_money_text(params, self.model.short_currency())
            self.view.set_wot_text(params)
            self.refresh_localized_data()

    def handle_identity_change(self, identity):
        if identity.pubkey == self.model.connection.pubkey and identity.uid == self.model.connection.uid:
            self.refresh_localized_data()

    def refresh_localized_data(self):
        """
        Refresh localized data in view
        """
        localized_data = self.model.get_localized_data()
        try:
            simple_data = self.model.get_identity_data()
            all_data = {**simple_data, **localized_data}
            self.view.set_simple_informations(all_data, InformationsView.CommunityState.READY)
        except NoPeerAvailable as e:
            self._logger.debug(str(e))
            self.view.set_simple_informations(all_data, InformationsView.CommunityState.OFFLINE)
        except errors.DuniterError as e:
            if e.ucode == errors.BLOCK_NOT_FOUND:
                self.view.set_simple_informations(all_data, InformationsView.CommunityState.NOT_INIT)
            else:
                self._logger.debug(str(e))

        self.view.set_general_text(localized_data)
        self.view.set_rules_text(localized_data)

