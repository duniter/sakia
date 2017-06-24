from PyQt5.QtWidgets import QDialog, QTabWidget, QVBoxLayout
from PyQt5.QtCore import QObject, pyqtSignal
from sakia.decorators import asyncify
from sakia.data.entities import Identity
from sakia.gui.widgets.dialogs import dialog_async_exec, QAsyncMessageBox
from .model import UserInformationModel
from .view import UserInformationView
import logging


class UserInformationController(QObject):
    """
    The homescreen view
    """
    identity_loaded = pyqtSignal(Identity)

    def __init__(self, parent, view, model):
        """
        Constructor of the homescreen component

        :param sakia.gui.homescreen.view.HomeScreenView: the view
        :param sakia.gui.homescreen.model.HomeScreenModel model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self._logger = logging.getLogger('sakia')

    @classmethod
    def create(cls, parent, app, identity):
        view = UserInformationView(parent.view if parent else None)
        model = UserInformationModel(None, app, identity)
        homescreen = cls(parent, view, model)
        model.setParent(homescreen)
        return homescreen

    @classmethod
    def show_identity(cls, parent, app, identity):
        dialog = QDialog()
        dialog.setWindowTitle("Informations")
        user_info = cls.create(parent, app, identity)
        user_info.view.setParent(dialog)
        dialog.setLayout(QVBoxLayout(dialog))
        dialog.layout().addWidget(user_info.view)
        user_info.refresh()
        dialog.resize(800, 300)
        dialog.exec()

    @classmethod
    @asyncify
    async def search_and_show_pubkey(cls, parent, app, pubkey):
        dialog = QDialog(parent)
        dialog.setWindowTitle("Informations")
        layout = QVBoxLayout(dialog)
        tabwidget = QTabWidget(dialog)
        layout.addWidget(tabwidget)

        identities = await app.identities_service.lookup(pubkey)
        for i in identities:
            user_info = cls.create(parent, app, i)
            user_info.refresh()
            tabwidget.addTab(user_info.view, i.uid)
        return await dialog_async_exec(dialog)

    @asyncify
    async def refresh(self):
        try:
            if self.model.identity:
                self.view.show_busy()
                await self.model.load_identity(self.model.identity)
                self.view.display_uid(self.model.identity.uid, self.model.identity.member)
                self.view.display_identity_timestamps(self.model.identity.pubkey, self.model.identity.timestamp,
                                                      self.model.identity.membership_timestamp,
                                                      self.model.mstime_remaining(), await self.model.nb_certs())
                self.view.hide_busy()
                self.identity_loaded.emit(self.model.identity)
        except RuntimeError as e:
            # object can be deleted by Qt during asynchronous ops
            # we don't care of this error
            if "wrapped C/C++ object" in str(e):
                self._logger.debug(str(e))
                pass
            else:
                raise

    @asyncify
    async def search_identity(self, identity):
        self.view.show_busy()
        await self.model.load_identity(identity)
        self.refresh()
        self.view.hide_busy()

    def clear(self):
        self.model.clear()
        self.view.clear()

    def change_identity(self, identity):
        """
        Set identity
        :param sakia.core.registry.Identity identity:
        """
        self.model.identity = identity
        self.refresh()
