from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QObject, pyqtSignal
from sakia.decorators import asyncify
from .model import UserInformationModel
from .view import UserInformationView


class UserInformationController(QObject):
    """
    The homescreen view
    """
    identity_loaded = pyqtSignal()

    def __init__(self, parent, view, model):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model

    @classmethod
    def create(cls, parent, app, currency, identity):
        view = UserInformationView(parent.view)
        model = UserInformationModel(None, app, currency, identity)
        homescreen = cls(parent, view, model)
        model.setParent(homescreen)
        return homescreen

    @classmethod
    def open_dialog(cls, parent, app, currency, identity):
        dialog = QDialog()
        user_info = cls.create(parent, app, currency, identity)
        user_info.view.setParent(dialog)
        user_info.refresh()
        dialog.exec()

    @asyncify
    async def refresh(self):
        if self.model.identity:
            self.view.show_busy()
            self.view.display_uid(self.model.identity.uid)
            await self.model.load_identity(self.model.identity)
            self.view.display_identity_timestamps(self.model.identity.pubkey, self.model.identity.timestamp,
                                                  self.model.identity.membership_timestamp)
            self.view.hide_busy()
            self.identity_loaded.emit()

    @asyncify
    async def search_identity(self, identity):
        await self.model.load_identity(identity)
        self.refresh()

    def change_identity(self, identity):
        """
        Set identity
        :param sakia.core.registry.Identity identity:
        """
        self.model.identity = identity
        self.refresh()

    def set_currency(self, currency):
        self.model.set_currency(currency)
        self.refresh()