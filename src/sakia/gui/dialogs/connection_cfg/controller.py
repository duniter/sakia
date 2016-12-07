import asyncio
import logging

from aiohttp.errors import DisconnectedError, ClientError, TimeoutError

from duniterpy.documents import MalformedDocumentError
from sakia.errors import NoPeerAvailable
from sakia.decorators import asyncify
from sakia.data.processors import IdentitiesProcessor, NodesProcessor
from sakia.data.connectors import BmaConnector
from sakia.gui.component.controller import ComponentController
from sakia.gui.password_asker import PasswordAskerDialog, detect_non_printable
from .model import ConnectionConfigModel
from .view import ConnectionConfigView


class ConnectionConfigController(ComponentController):
    """
    The AccountConfigController view
    """

    CONNECT = 0
    REGISTER = 1
    GUEST = 2

    def __init__(self, parent, view, model):
        """
        Constructor of the AccountConfigController component

        :param sakia.gui.account_cfg.view.AccountConfigCView: the view
        :param sakia.gui.account_cfg.model.AccountConfigModel model: the model
        """
        super().__init__(parent, view, model)

        self.step_node = asyncio.Future()
        self.step_key = asyncio.Future()
        self.view.button_connect.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.CONNECT))
        self.view.button_register.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.REGISTER))
        self.view.button_guest.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.GUEST))
        self.password_asker = None
        self.view.values_changed.connect(self.check_key)
        self._logger = logging.getLogger('sakia')

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a AccountConfigController component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.app.Application app:
        :return: a new AccountConfigController controller
        :rtype: AccountConfigController
        """
        view = ConnectionConfigView(parent.view if parent else None)
        model = ConnectionConfigModel(None, app, None,
                                      IdentitiesProcessor(app.db.identities_repo, app.db.blockchains_repo,
                                                          BmaConnector(NodesProcessor(app.db.nodes_repo))))
        account_cfg = cls(parent, view, model)
        model.setParent(account_cfg)
        return account_cfg

    @classmethod
    def create_connection(cls, parent, app):
        """
        Open a dialog to create a new account
        :param parent:
        :param app:
        :return:
        """
        connection_cfg = cls.create(parent, app, account=None)
        connection_cfg.view.set_creation_layout()
        asyncio.ensure_future(connection_cfg.process())
        connection_cfg.view.exec()

    @classmethod
    def modify_connection(cls, parent, app, connection):
        """
        Open a dialog to modify an existing account
        :param parent:
        :param app:
        :param account:
        :return:
        """
        connection_cfg = cls.create(parent, app, connection=connection)
        #connection_cfg.view.set_modification_layout(account.name)
        connection_cfg._current_step = 1

    def init_nodes_page(self):
        self.view.set_steps_buttons_visible(True)
        model = self.model.init_nodes_model()
        self.view.tree_peers.customContextMenuRequested(self.show_context_menu)

        self.view.set_nodes_model(model)
        self.view.button_previous.setEnabled(False)
        self.view.button_next.setText(self.config_dialog.tr("Ok"))

    def init_name_page(self):
        """
        Initialize an account name page
        """
        if self.model.connection:
            self.view.set_account_name(self.model.connection.uid)

        self.view.button_previous.setEnabled(False)
        self.view.button_next.setEnabled(False)

    def check_name(self):
        return len(self.view.edit_account_name.text()) > 2

    async def process(self):
        self._logger.debug("Begin process")
        while not self.model.connection:
            mode = await self.step_node
            self._logger.debug("Create connection")
            try:
                self.view.button_connect.setEnabled(False)
                self.view.button_register.setEnabled(False)
                await self.model.create_connection(self.view.lineedit_server.text(),
                                                   self.view.spinbox_port.value(),
                                                   self.view.checkbox_secured.isChecked())
                self.password_asker = PasswordAskerDialog(self.model.connection)
            except (DisconnectedError, ClientError, MalformedDocumentError, ValueError, TimeoutError) as e:
                self._logger.debug(str(e))
                self.view.display_info(self.tr("Could not connect. Check hostname, ip address or port : </br>str(e)"))
                self.step_node = asyncio.Future()
                self.view.button_connect.setEnabled(True)
                self.view.button_register.setEnabled(True)

        self._logger.debug("Key step")
        self.view.set_currency(self.model.connection.currency)
        if mode == ConnectionConfigController.REGISTER:
            self._logger.debug("Registering mode")
            self.view.button_next.clicked.connect(self.check_register)
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            await self.step_key
        elif mode == ConnectionConfigController.CONNECT:
            self._logger.debug("Connect mode")
            self.view.button_next.clicked.connect(self.check_connect)
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key

        self.model.insert_or_update_connection()
        self.view.stacked_pages.setCurrentWidget(self.view.page_services)
        self.view.progress_bar.setValue(0)
        self.view.progress_bar.setMaximum(3)
        await self.model.initialize_blockchain(self.view.stream_log)
        self.view.progress_bar.setValue(1)

        if mode in (ConnectionConfigController.REGISTER, ConnectionConfigController.CONNECT):
            self.view.stream_log("Saving identity...")
            self.model.insert_or_update_identity(connection_identity)
            self.view.stream_log("Initializing identity informations...")
            await self.model.initialize_identity(connection_identity, log_stream=self.view.stream_log)
            self.view.stream_log("Initializing certifications informations...")
            await self.model.initialize_certifications(connection_identity, log_stream=self.view.stream_log)
            self.view.stream_log("Initializing transactions history...")
            await self.model.initialize_transactions(connection_identity, log_stream=self.view.stream_log)

        self.view.progress_bar.setValue(2)
        if mode == ConnectionConfigController.REGISTER:
            self.view.display_info(self.tr("Broadcasting identity..."))
            self.view.stream_log("Broadcasting identity...")
            password = await self.password_asker.async_exec()
            result, connection_identity = await self.model.publish_selfcert(self.model.connection.salt, password)
            if result[0]:
                self.view.show_success(self.model.notification())
            else:
                self.view.show_error(self.model.notification(), result[1])

        self.view.progress_bar.setValue(3)
        await self.model.initialize_sources(self.view.stream_log)

        self._logger.debug("Validate changes")
        self.model.app.db.commit()
        self.accept()

    def check_key(self):
        if self.model.app.parameters.expert_mode:
            return True

        if len(self.view.edit_salt.text()) < 6:
            self.view.label_info.setText(self.tr("Forbidden : salt is too short"))
            return False

        if len(self.view.edit_password.text()) < 6:
            self.view.label_info.setText(self.tr("Forbidden : password is too short"))
            return False

        if detect_non_printable(self.view.edit_salt.text()):
            self.view.label_info.setText(self.tr("Forbidden : Invalid characters in salt field"))
            return False

        if detect_non_printable(self.view.edit_password.text()):
            self.view.label_info.setText(
                self.tr("Forbidden : Invalid characters in password field"))
            return False

        if self.view.edit_password.text() != \
                self.view.edit_password_repeat.text():
            self.view.label_info.setText(self.tr("Error : passwords are different"))
            return False

        if self.view.edit_salt.text() != \
                self.view.edit_salt_bis.text():
            self.view.label_info.setText(self.tr("Error : secret keys are different"))
            return False

        self.view.label_info.setText("")
        return True

    @asyncify
    async def check_connect(self, checked=False):
        self._logger.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            salt = self.view.edit_salt.text()
            password = self.view.edit_password.text()
            self.model.set_scrypt_infos(salt, password, self.view.scrypt_params)
            self.model.set_uid(self.view.edit_account_name.text())
            registered, found_identity = await self.model.check_registered()
            self.view.button_connect.setEnabled(True)
            self.view.button_register.setEnabled(True)
            if registered[0] is False and registered[2] is None:
                self.view.display_info(self.tr("Could not find your identity on the network."))
            elif registered[0] is False and registered[2]:
                self.view.display_info(self.tr("""Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
            else:
                self.step_key.set_result(found_identity)
        except NoPeerAvailable:
            self.config_dialog.label_error.setText(self.tr("Could not connect. Check node peering entry"))

    @asyncify
    async def check_register(self, checked=False):
        self._logger.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            salt = self.view.edit_salt.text()
            password = self.view.edit_password.text()
            self.model.set_scrypt_infos(salt, password, self.view.scrypt_params)
            self.model.set_uid(self.view.edit_account_name.text())
            registered, found_identity = await self.model.check_registered()
            if registered[0] is False and registered[2] is None:
                self.step_key.set_result(None)
            elif registered[0] is False and registered[2]:
                self.view.display_info(self.tr("""Your pubkey or UID was already found on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
            else:
                self.view.display_info("Your account already exists on the network")
        except NoPeerAvailable:
            self.view.display_info(self.tr("Could not connect. Check node peering entry"))

    @asyncify
    async def accept(self):
        self.view.accept()

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        self.refresh()
        return future

    @property
    def view(self) -> ConnectionConfigView:
        return self._view

    @property
    def model(self) -> ConnectionConfigModel:
        return self._model