import asyncio
import logging

from aiohttp.errors import DisconnectedError, ClientError, TimeoutError
from duniterpy.documents import MalformedDocumentError
from duniterpy.api.errors import DuniterError
from sakia.errors import NoPeerAvailable
from sakia.decorators import asyncify
from sakia.data.processors import IdentitiesProcessor, NodesProcessor
from sakia.data.connectors import BmaConnector
from sakia.gui.password_asker import PasswordAskerDialog, detect_non_printable
from .model import ConnectionConfigModel
from .view import ConnectionConfigView
from PyQt5.QtCore import QObject


class ConnectionConfigController(QObject):
    """
    The AccountConfigController view
    """

    CONNECT = 0
    REGISTER = 1
    WALLET = 2

    def __init__(self, parent, view, model):
        """
        Constructor of the AccountConfigController component

        :param sakia.gui.dialogs.connection_cfg.view.ConnectionConfigView: the view
        :param sakia.gui.dialogs.connection_cfg.model.ConnectionConfigView model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model

        self.step_node = asyncio.Future()
        self.step_key = asyncio.Future()
        self.view.button_connect.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.CONNECT))
        self.view.button_register.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.REGISTER))
        self.view.button_wallet.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.WALLET))
        self.password_asker = None
        self.view.values_changed.connect(lambda: self.view.button_next.setEnabled(self.check_key()))
        self.view.values_changed.connect(lambda: self.view.button_generate.setEnabled(self.check_key()))
        self._logger = logging.getLogger('sakia')

    @classmethod
    def create(cls, parent, app):
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
                                                          BmaConnector(NodesProcessor(app.db.nodes_repo),
                                                                       app.parameters)))
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
        connection_cfg = cls.create(parent, app)
        connection_cfg.view.set_creation_layout()
        asyncio.ensure_future(connection_cfg.process())
        return connection_cfg

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
        if self.model.connection:
            mode = await self.step_node
        else:
            while not self.model.connection:
                mode = await self.step_node
                self._logger.debug("Create connection")
                try:
                    self.view.button_connect.setEnabled(False)
                    self.view.button_register.setEnabled(False)
                    await self.model.create_connection()
                    self.password_asker = PasswordAskerDialog(self.model.connection)
                except (DisconnectedError, ClientError, MalformedDocumentError, ValueError, TimeoutError) as e:
                    self._logger.debug(str(e))
                    self.view.display_info(self.tr("Could not connect. Check hostname, ip address or port : <br/>"
                                                   + str(e)))
                    self.step_node = asyncio.Future()
                    self.view.button_connect.setEnabled(True)
                    self.view.button_register.setEnabled(True)

        self._logger.debug("Key step")
        self.view.set_currency(self.model.connection.currency)
        if mode == ConnectionConfigController.REGISTER:
            self._logger.debug("Registering mode")
            self.view.button_next.clicked.connect(self.check_register)
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key
        elif mode == ConnectionConfigController.CONNECT:
            self._logger.debug("Connect mode")
            self.view.button_next.clicked.connect(self.check_connect)
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key
        elif mode == ConnectionConfigController.WALLET:
            self._logger.debug("Wallet mode")
            self.view.button_next.clicked.connect(self.check_wallet)
            self.view.edit_uid.hide()
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key

        self.view.stacked_pages.setCurrentWidget(self.view.page_services)
        self.view.progress_bar.setValue(0)
        self.view.progress_bar.setMaximum(3)
        try:
            await self.model.initialize_blockchain(self.view.stream_log)
            self.view.progress_bar.setValue(1)

            if mode == ConnectionConfigController.REGISTER:
                self.view.display_info(self.tr("Broadcasting identity..."))
                self.view.stream_log("Broadcasting identity...")
                result, connection_identity = await self.model.publish_selfcert()
                if result[0]:
                    await self.view.show_success(self.model.notification())
                else:
                    self.view.show_error(self.model.notification(), result[1])
                    raise StopIteration()

            self.view.progress_bar.setValue(2)

            if mode in (ConnectionConfigController.REGISTER, ConnectionConfigController.CONNECT):
                self.view.stream_log("Saving identity...")
                self.model.connection.blockstamp = connection_identity.blockstamp
                self.model.insert_or_update_connection()
                self.model.insert_or_update_identity(connection_identity)
                self.view.stream_log("Initializing identity informations...")
                await self.model.initialize_identity(connection_identity, log_stream=self.view.stream_log)
                self.view.stream_log("Initializing certifications informations...")
                await self.model.initialize_certifications(connection_identity, log_stream=self.view.stream_log)

            if mode in (ConnectionConfigController.REGISTER,
                        ConnectionConfigController.CONNECT,
                        ConnectionConfigController.WALLET):
                self.view.stream_log("Initializing transactions history...")
                transactions = await self.model.initialize_transactions(self.model.connection, log_stream=self.view.stream_log)
                self.view.stream_log("Initializing dividends history...")
                await self.model.initialize_dividends(self.model.connection, transactions, log_stream=self.view.stream_log)

            self.view.progress_bar.setValue(3)
            await self.model.initialize_sources(self.view.stream_log)

            self._logger.debug("Validate changes")
            self.model.insert_or_update_connection()
            self.model.app.db.commit()
        except (NoPeerAvailable, DuniterError, StopIteration) as e:
            if not isinstance(e, StopIteration):
                self.view.show_error(self.model.notification(), str(e))
            self._logger.debug(str(e))
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            self.step_node = asyncio.Future()
            self.step_node.set_result(mode)
            self.step_key = asyncio.Future()
            self.view.button_next.disconnect()
            self.view.edit_uid.show()
            asyncio.ensure_future(self.process())
            return
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
    async def check_wallet(self, checked=False):
        self._logger.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            salt = self.view.edit_salt.text()
            password = self.view.edit_password.text()
            self.model.set_scrypt_infos(salt, password, self.view.scrypt_params)
            self.model.set_uid("")
            if not self.model.key_exists():
                try:
                    registered, found_identity = await self.model.check_registered()
                    self.view.button_connect.setEnabled(True)
                    self.view.button_register.setEnabled(True)
                    if registered[0] is False and registered[2] is None:
                        self.step_key.set_result(None)
                    elif registered[2]:
                        self.view.display_info(self.tr("""Your pubkey is associated to a pubkey.
        Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
                except DuniterError as e:
                    self.view.display_info(e.message)
                except NoPeerAvailable as e:
                    self.view.display_info(str(e))
            else:
                self.view.display_info(self.tr("A connection already exists using this key."))

        except NoPeerAvailable:
            self.config_dialog.label_error.setText(self.tr("Could not connect. Check node peering entry"))

    @asyncify
    async def check_connect(self, checked=False):
        self._logger.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            salt = self.view.edit_salt.text()
            password = self.view.edit_password.text()
            self.model.set_scrypt_infos(salt, password, self.view.scrypt_params)
            self.model.set_uid(self.view.edit_uid.text())
            if not self.model.key_exists():
                try:
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
                except DuniterError as e:
                    self.view.display_info(e.message)
                except NoPeerAvailable as e:
                    self.view.display_info(str(e))
            else:
                self.view.display_info(self.tr("A connection already exists using this key."))

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
            self.model.set_uid(self.view.edit_uid.text())
            if not self.model.key_exists():
                try:
                    registered, found_identity = await self.model.check_registered()
                    if registered[0] is False and registered[2] is None:
                        self.step_key.set_result(None)
                    elif registered[0] is False and registered[2]:
                        self.view.display_info(self.tr("""Your pubkey or UID was already found on the network.
        Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
                    else:
                        self.view.display_info("Your account already exists on the network")
                except DuniterError as e:
                    self.view.display_info(e.message)
                except NoPeerAvailable as e:
                    self.view.display_info(str(e))
            else:
                self.view.display_info(self.tr("A connection already exists using this key."))
        except NoPeerAvailable:
            self.view.display_info(self.tr("Could not connect. Check node peering entry"))

    @asyncify
    async def accept(self):
        self.view.accept()

    def async_exec(self):
        future = asyncio.Future()
        self.view.finished.connect(lambda r: future.set_result(r))
        self.view.open()
        return future

    def exec(self):
        return self.view.exec()