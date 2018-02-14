import asyncio
import logging

from PyQt5.QtCore import QObject, Qt
from aiohttp import ClientError
from asyncio import TimeoutError

from sakia.gui.widgets.dialogs import dialog_async_exec, QAsyncFileDialog, QMessageBox
from duniterpy.api.errors import DuniterError
from duniterpy.documents import MalformedDocumentError
from sakia.data.connectors import BmaConnector
from sakia.data.processors import IdentitiesProcessor, NodesProcessor
from sakia.decorators import asyncify
from sakia.errors import NoPeerAvailable
from sakia.helpers import detect_non_printable
from .model import ConnectionConfigModel
from .view import ConnectionConfigView


class ConnectionConfigController(QObject):
    """
    The AccountConfigController view
    """

    CONNECT = 0
    REGISTER = 1
    WALLET = 2
    PUBKEY = 3

    def __init__(self, parent, view, model):
        """
        Constructor of the AccountConfigController component

        :param sakia.gui.dialogs.connection_cfg.view.ConnectionConfigView: the view
        :param sakia.gui.dialogs.connection_cfg.model.ConnectionConfigView model: the model
        """
        super().__init__(parent)
        self.view = view
        self.model = model
        self.mode = -1

        self.step_node = asyncio.Future()
        self.step_licence = asyncio.Future()
        self.step_key = asyncio.Future()
        self.view.button_connect.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.CONNECT))
        self.view.button_register.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.REGISTER))
        self.view.button_wallet.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.WALLET))
        self.view.button_pubkey.clicked.connect(
            lambda: self.step_node.set_result(ConnectionConfigController.PUBKEY))
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
                                      IdentitiesProcessor.instanciate(app))
        account_cfg = cls(parent, view, model)
        model.setParent(account_cfg)
        view.set_license(app.currency)
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
        connection_cfg.view.set_creation_layout(app.currency)
        asyncio.ensure_future(connection_cfg.process())
        return connection_cfg

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
            self.mode = await self.step_node
        else:
            while not self.model.connection:
                self.mode = await self.step_node
                self._logger.debug("Create connection")
                try:
                    self.view.button_connect.setEnabled(False)
                    self.view.button_register.setEnabled(False)
                    await self.model.create_connection()
                except (ClientError, MalformedDocumentError, ValueError, TimeoutError) as e:
                    self._logger.debug(str(e))
                    self.view.display_info(self.tr("Could not connect. Check hostname, ip address or port : <br/>"
                                                   + str(e)))
                    self.step_node = asyncio.Future()
                    self.view.button_connect.setEnabled(True)
                    self.view.button_register.setEnabled(True)

        self._logger.debug("Licence step")
        self.view.stacked_pages.setCurrentWidget(self.view.page_licence)
        self.view.button_accept.clicked.connect(lambda: self.step_licence.set_result(True))
        await self.step_licence
        self.view.button_accept.disconnect()
        self._logger.debug("Key step")
        self.view.set_currency(self.model.connection.currency)
        connection_identity = None
        self.view.button_next.setEnabled(self.check_key())

        if self.mode == ConnectionConfigController.REGISTER:
            self._logger.debug("Registering mode")
            self.view.groupbox_pubkey.hide()
            self.view.button_next.clicked.connect(self.check_register)
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key
        elif self.mode == ConnectionConfigController.CONNECT:
            self._logger.debug("Connect mode")
            self.view.button_next.setText(self.tr("Next"))
            self.view.groupbox_pubkey.hide()
            self.view.button_next.clicked.connect(self.check_connect)
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key
        elif self.mode == ConnectionConfigController.WALLET:
            self._logger.debug("Wallet mode")
            self.view.button_next.setText(self.tr("Next"))
            self.view.button_next.clicked.connect(self.check_wallet)
            self.view.edit_uid.hide()
            self.view.label_action.hide()
            self.view.groupbox_pubkey.hide()
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key
        elif self.mode == ConnectionConfigController.PUBKEY:
            self._logger.debug("Pubkey mode")
            self.view.button_next.setText(self.tr("Next"))
            self.view.button_next.clicked.connect(self.check_pubkey)
            if not self.view.label_action.text().endswith(self.tr(" (Optional)")):
                self.view.label_action.setText(self.view.label_action.text() + self.tr(" (Optional)"))
            self.view.groupbox_key.hide()
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            connection_identity = await self.step_key

        self.view.stacked_pages.setCurrentWidget(self.view.page_services)
        self.view.set_progress_steps(6)
        try:
            if self.mode == ConnectionConfigController.REGISTER:
                self.view.display_info(self.tr("Broadcasting identity..."))
                self.view.stream_log("Broadcasting identity...")
                result = await self.model.publish_selfcert(connection_identity)
                if result[0]:
                    await self.view.show_success(self.model.notification())
                else:
                    self.view.show_error(self.model.notification(), result[1])
                    raise StopIteration()

            self.view.set_step(1)

            if self.mode in (ConnectionConfigController.REGISTER,
                             ConnectionConfigController.CONNECT,
                             ConnectionConfigController.PUBKEY) and connection_identity:
                self.view.stream_log("Saving identity...")
                self.model.connection.blockstamp = connection_identity.blockstamp
                self.model.insert_or_update_connection()
                self.model.insert_or_update_identity(connection_identity)
                self.view.stream_log("Initializing identity informations...")
                await self.model.initialize_identity(connection_identity,
                                                     log_stream=self.view.stream_log,
                                                     progress=self.view.progress)
                self.view.stream_log("Initializing certifications informations...")
                self.view.set_step(2)
                await self.model.initialize_certifications(connection_identity,
                                                           log_stream=self.view.stream_log,
                                                           progress=self.view.progress)

            self.view.set_step(3)
            self.view.stream_log("Initializing transactions history...")
            transactions = await self.model.initialize_transactions(self.model.connection,
                                                                    log_stream=self.view.stream_log,
                                                                    progress=self.view.progress)
            self.view.set_step(4)
            self.view.stream_log("Initializing dividends history...")
            dividends = await self.model.initialize_dividends(self.model.connection, transactions,
                                                              log_stream=self.view.stream_log,
                                                              progress=self.view.progress)

            self.view.set_step(5)
            await self.model.initialize_sources(transactions, dividends,
                                                log_stream=self.view.stream_log,
                                                progress=self.view.progress)

            self.view.set_step(6)
            self._logger.debug("Validate changes")
            self.model.insert_or_update_connection()
            self.model.app.db.commit()

            if self.mode == ConnectionConfigController.REGISTER:
                await self.view.show_register_message(self.model.blockchain_parameters())
        except (NoPeerAvailable, DuniterError, StopIteration) as e:
            if not isinstance(e, StopIteration):
                self.view.show_error(self.model.notification(), str(e))
            self._logger.debug(str(e))
            self.view.stacked_pages.setCurrentWidget(self.view.page_connection)
            self.step_node = asyncio.Future()
            self.step_node.set_result(self.mode)
            self.step_key = asyncio.Future()
            self.view.button_next.disconnect()
            self.view.edit_uid.show()
            asyncio.ensure_future(self.process())
            return
        self.accept()

    def check_key(self):
        if self.mode == ConnectionConfigController.PUBKEY:
            if len(self.view.edit_pubkey.text()) < 42:
                self.view.label_info.setText(self.tr("Forbidden : pubkey is too short"))
                return False
            if len(self.view.edit_pubkey.text()) > 45:
                self.view.label_info.setText(self.tr("Forbidden : pubkey is too long"))
                return False
        else:
            if self.view.edit_password.text() != \
                    self.view.edit_password_repeat.text():
                self.view.label_info.setText(self.tr("Error : passwords are different"))
                return False

            if self.view.edit_salt.text() != \
                    self.view.edit_salt_bis.text():
                self.view.label_info.setText(self.tr("Error : secret keys are different"))
                return False

            if detect_non_printable(self.view.edit_salt.text()):
                self.view.label_info.setText(self.tr("Forbidden : Invalid characters in salt field"))
                return False

            if detect_non_printable(self.view.edit_password.text()):
                self.view.label_info.setText(
                    self.tr("Forbidden : Invalid characters in password field"))
                return False

            if self.model.app.parameters.expert_mode:
                self.view.label_info.setText(
                    self.tr(""))
                return True

            if len(self.view.edit_salt.text()) < 6:
                self.view.label_info.setText(self.tr("Forbidden : salt is too short"))
                return False

            if len(self.view.edit_password.text()) < 6:
                self.view.label_info.setText(self.tr("Forbidden : password is too short"))
                return False

        self.view.label_info.setText("")
        return True

    async def action_save_revocation(self):
        raw_document, identity = self.model.generate_revocation()
        # Testable way of using a QFileDialog
        selected_files = await QAsyncFileDialog.get_save_filename(self.view, self.tr("Save a revocation document"),
                                                                  "", self.tr("All text files (*.txt)"))
        if selected_files:
            path = selected_files[0]
            if not path.endswith('.txt'):
                path = "{0}.txt".format(path)
            with open(path, 'w') as save_file:
                save_file.write(raw_document)

            dialog = QMessageBox(QMessageBox.Information, self.tr("Revokation file"),
                                 self.tr("""<div>Your revocation document has been saved.</div>
<div><b>Please keep it in a safe place.</b></div>
The publication of this document will remove your identity from the network.</p>"""), QMessageBox.Ok)
            dialog.setTextFormat(Qt.RichText)
            return True, identity
        return False, identity

    @asyncify
    async def check_pubkey(self, checked=False):
        self._logger.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            self.model.set_pubkey(self.view.edit_pubkey.text(), self.view.scrypt_params)
            self.model.set_uid(self.view.edit_uid.text())
            if not self.model.key_exists():
                try:
                    registered, found_identity = await self.model.check_registered()
                    self.view.button_connect.setEnabled(True)
                    self.view.button_register.setEnabled(True)
                    if self.view.edit_uid.text():
                        if registered[0] is False and registered[2] is None:
                            self.view.display_info(self.tr("Could not find your identity on the network."))
                        elif registered[0] is False and registered[2]:
                            self.view.display_info(self.tr("""Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
                        else:
                            self.step_key.set_result(found_identity)
                    else:
                        self.step_key.set_result(None)

                except DuniterError as e:
                    self.view.display_info(e.message)
                except NoPeerAvailable as e:
                    self.view.display_info(str(e))
            else:
                self.view.display_info(self.tr("A connection already exists using this key."))

        except NoPeerAvailable:
            self.config_dialog.label_error.setText(self.tr("Could not connect. Check node peering entry"))

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
                        self.view.display_info(self.tr("""Your pubkey is associated to an identity.
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
                        result, identity = await self.action_save_revocation()
                        if result:
                            self.step_key.set_result(identity)
                        else:
                            self.view.display_info("Saving your revocation document on your disk is mandatory.")
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