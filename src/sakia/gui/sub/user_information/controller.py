from PyQt5.QtWidgets import QDialog

from sakia.decorators import asyncify
from sakia.gui.component.controller import ComponentController
from .model import UserInformationModel
from .view import UserInformationView


class UserInformationController(ComponentController):
    """
    The homescreen view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent, view, model)

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a homescreen component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new Homescreen controller
        :rtype: UserInformationController
        """
        currency = kwargs['currency']
        identity = kwargs['identity']
        view = UserInformationView(parent.view)
        model = UserInformationModel(None, app, currency, identity)
        homescreen = cls(parent, view, model)
        model.setParent(homescreen)
        return homescreen

    @classmethod
    def open_dialog(cls, parent, app, currency, identity):
        dialog = QDialog()
        user_info = cls.create(parent, app, currency=currency, identity=identity)
        user_info.view.setParent(dialog)
        user_info.refresh()
        dialog.exec()

    @classmethod
    def as_widget(cls, parent, app, currency, identity):
        return cls(app, currency, identity)

    @asyncify
    async def refresh(self):
        if self.model.identity:
            self.view.show_busy()
            self.view.display_uid(self.model.identity.uid)
            await self.model.load_identity()
            self.view.display_identity_timestamps(self.model.identity.pubkey, self.model.identity.timestamp,
                                                  self.model.identity.membership_timestamp)
            self.view.hide_busy()

    @asyncify
    async def search_identity(self, pubkey):
        """
        Set identity
        :param str pubkey: the pubkey
        """
        await self.model.search_identity(pubkey)
        self.refresh()

    def change_identity(self, identity):
        """
        Set identity
        :param sakia.core.registry.Identity identity:
        """
        self.model.identity = identity
        self.refresh()

    @property
    def view(self) -> UserInformationView:
        return self._view

    @property
    def model(self) -> UserInformationModel:
        return self._model