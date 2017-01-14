import asyncio

from PyQt5.QtCore import QObject
from duniterpy.documents import MalformedDocumentError
from sakia.decorators import asyncify
from .model import RevocationModel
from .view import RevocationView


class RevocationController(QObject):
    """
    The revocation view
    """

    def __init__(self, view, model):
        """
        Constructor of the revocation component

        :param sakia.gui.dialogs.revocation.view.revocationView: the view
        :param sakia.gui.dialogs.revocation.model.revocationModel model: the model
        """
        super().__init__()
        self.view = view
        self.model = model

        self.view.button_next.clicked.connect(lambda checked: self.handle_next_step(False))
        self.view.button_load.clicked.connect(self.load_from_file)
        self.view.spinbox_port.valueChanged.connect(self.refresh_revocation_info)
        self.view.edit_address.textChanged.connect(self.refresh_revocation_info)
        self.view.radio_address.toggled.connect(self.refresh_revocation_info)
        self.view.radio_currency.toggled.connect(self.refresh_revocation_info)

        self._steps = (
            {
                'page': self.view.page_load_file,
                'init': lambda: None,
                'next': lambda: None
            },
            {
                'page': self.view.page_destination,
                'init': self.init_publication_page,
                'next': self.publish
            }
        )
        self._current_step = 0

    @classmethod
    def create(cls, parent, app, connection):
        """
        Instanciate a revocation component
        :param sakia.app.Application app:
        :return: a new revocation controller
        :rtype: revocationController
        """
        view = RevocationView(parent.view)
        model = RevocationModel(app, connection)
        revocation = cls(view, model)
        return revocation

    @classmethod
    def open_dialog(cls, parent, app, connection):
        """
        Certify and identity
        :param sakia.gui.component.controller.ComponentController parent: the parent
        :param sakia.app.Application app: the application
        :param sakia.data.entities.Connection connection: the connection certifying the identity
        :return:
        """
        dialog = cls.create(parent, app, connection=connection)
        dialog.handle_next_step(init=True)
        return dialog.exec()

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
            self.view.show_revoked_selfcert(self.model.revoked_identity)
            self.view.button_next.setEnabled(True)
        except FileNotFoundError:
            pass
        except MalformedDocumentError:
            self.view.malformed_file_error()
            self.button_next.setEnabled(False)

    def refresh_revocation_info(self):
        self.view.refresh_revocation_label(self.model.revoked_identity)

    def init_publication_page(self):
        communities_names = self.model.currencies_names()
        self.view.set_currencies_names(communities_names)

    def publish(self):
        self.view.button_next.setEnabled(False)
        if self.view.ask_for_confirmation():
            self.accept()
        else:
            self.view.button_next.setEnabled(True)

    @asyncify
    async def accept(self):
        if self.view.radio_currency.isChecked():
            index = self.view.combo_currency.currentIndex()
            result, error = await self.model.broadcast_to_network(index)
        else:
            server = self.view.edit_address.text()
            port = self.view.spinbox_port.value()
            secured = self.view.checkbox_secured.isChecked()
            result, error = await self.model.send_to_node(server, port, secured)

        if result:
            self.view.accept()
        else:
            await self.view.revocation_broadcast_error(error)

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        self.refresh()
        return future

    def exec(self):
        self.view.exec()
