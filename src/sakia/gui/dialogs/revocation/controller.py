from sakia.gui.component.controller import ComponentController
from .view import RevocationView
from .model import RevocationModel
from duniterpy.documents import MalformedDocumentError
from sakia.tools.decorators import asyncify
import asyncio


class RevocationController(ComponentController):
    """
    The revocation view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the revocation component

        :param sakia.gui.revocation.view.revocationView: the view
        :param sakia.gui.revocation.model.revocationModel model: the model
        """
        super().__init__(parent, view, model)

        self.handle_next_step(init=True)
        self.view.button_next.clicked.connect(lambda checked: self.handle_next_step(False))
        self._steps = (
            {
                'page': self.view.page_load_file,
                'init': self.init_dialog,
                'next': self.revocation_selected
            },
            {
                'page': self.view.page_destination,
                'init': self.init_publication_page,
                'next': self.publish
            }
        )
        self._current_step = 0

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a revocation component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new revocation controller
        :rtype: revocationController
        """
        account = kwargs['account']
        view = RevocationView(parent.view)
        model = RevocationModel(None, app, account)
        revocation = cls(parent, view, model)
        model.setParent(revocation)
        return revocation

    @classmethod
    def open_dialog(cls, parent, app, account):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.core.Application app: the application
        :param sakia.core.Account account: the account certifying the identity
        :return:
        """
        dialog = cls.create(parent, app, account=account)
        dialog.refresh()
        return dialog.exec()

    @property
    def view(self) -> RevocationView:
        return self._view

    @property
    def model(self) -> RevocationModel:
        return self._model

    def handle_next_step(self, init=False):
        if self._current_step < len(self._steps) - 1:
            if not init:
                self.view.button_next.clicked.disconnect(self._steps[self._current_step]['next'])
                self._current_step += 1
            self._steps[self._current_step]['init']()
            self.view.stackedWidget.setCurrentWidget(self._steps[self._current_step]['page'])
            self.view.button_next.clicked.connect(self._steps[self._current_step]['next'])

    def load_from_file(self):
        selected_file = self.view.select_revocation_file()
        try:
            self.model.load_revocation(selected_file)
        except FileNotFoundError:
            pass
        except MalformedDocumentError:
            self.view.malformed_file_error()
            self.button_next.setEnabled(False)

    def revocation_selected(self):
        pass

    def init_publication_page(self):
        communities_names = self.model.communities_names()
        self.view.set_communities_names(communities_names)

    def publish(self):
        self.view.button_next.setEnabled(False)
        if self.view.ask_for_confirmation():
            self.accept()
        else:
            self.view.button_next.setEnabled(True)

    @asyncify
    async def accept(self):
        if self.view.radio_community.isChecked():
            index = self.view.combo_community.currentIndex()
            result, error = await self.model.send_to_community(index)
        else:
            server = self.view.edit_address.text()
            port = self.view.spinbox_port.value()
            result, error = await self.model.send_to_node(server, port)

        if result:
            self.view.accept()
        else:
            await self.view.revocation_broadcast_error(error)

    def async_exec(self):
        future = asyncio.Future()
        self.widget.finished.connect(lambda r: future.set_result(r))
        self.widget.open()
        self.refresh()
        return future

    def exec(self):
        self.widget.exec()
