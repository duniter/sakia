import logging

from PyQt5.QtGui import QCursor
from PyQt5.QtWidgets import QDialog, QApplication, QMenu
from aiohttp.errors import DisconnectedError, ClientError, TimeoutError
from sakia.errors import NoPeerAvailable

from duniterpy.documents import MalformedDocumentError
from sakia.decorators import asyncify
from sakia.gui.component.controller import ComponentController
from .model import CommunityConfigModel
from .view import CommunityConfigView


class CommunityConfigController(ComponentController):
    """
    The CommunityConfigController view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the CommunityConfigController component

        :param sakia.gui.community_cfg.view.CommunityConfigView: the view
        :param sakia.gui.community_cfg.model.CommunityConfigModel model: the model
        """
        super().__init__(parent, view, model)

        self._current_step = 0
        self.view.button_next.clicked.connect(lambda checked: self.handle_next_step(False))
        self._steps = (
            {
                'page': self.view.page_node,
                'init': self.init_connect_page,
                'next': lambda: True
            },
            {
                'page': self.view.page_add_nodes,
                'init': self.init_nodes_page,
                'next': self.accept
            }
        )
        self.handle_next_step(init=True)
        self.password_asker = None

        self.view.button_connect.clicked.connect(self.check_connect)
        self.view.button_register.clicked.connect(self.check_register)
        self.view.button_guest.clicked.connect(self.check_guest)

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a CommunityConfigController component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new CommunityConfigController controller
        :rtype: CommunityConfigController
        """
        account = kwargs['account']
        community = kwargs['community']
        password_asker = kwargs['password_asker']
        view = CommunityConfigView(parent.view)
        model = CommunityConfigModel(None, app, account, community)
        community_cfg = cls(parent, view, model)
        model.setParent(community_cfg)
        community_cfg.password_asker = password_asker
        return community_cfg

    @classmethod
    @asyncify
    def create_community(cls, parent, app, account, password_asker):
        """
        Open a dialog to create a new Community
        :param parent:
        :param app:
        :param account:
        :return:
        """
        community_cfg = cls.create(parent, app, account=account, community=None, password_asker=password_asker)
        community_cfg.view.set_creation_layout()
        return community_cfg.view.async_exec()

    @classmethod
    @asyncify
    def modify_community(cls, parent, app, account, community, password_asker):
        """
        Open a dialog to modify an existing Community
        :param parent:
        :param app:
        :param account:
        :param community:
        :return:
        """
        community_cfg = cls.create(parent, app, account=account,
                                   community=community, password_asker=password_asker)
        community_cfg.view.set_modification_layout(community.name)
        community_cfg._current_step = 1
        return community_cfg.view.async_exec()

    def handle_next_step(self, init=False):
        if self._current_step < len(self._steps) - 1:
            if not init:
                self._steps[self._current_step]['next']()
                self._current_step += 1
            self._steps[self._current_step]['init']()
            self.view.stacked_pages.setCurrentWidget(self._steps[self._current_step]['page'])

    def init_connect_page(self):
        pass

    def init_nodes_page(self):
        self.view.set_steps_buttons_visible(True)
        model = self.model.init_nodes_model()
        self.view.tree_peers.customContextMenuRequested(self.show_context_menu)

        self.view.set_nodes_model(model)
        self.view.button_previous.setEnabled(False)
        self.view.button_next.setText(self.config_dialog.tr("Ok"))

    @asyncify
    async def check_guest(self, checked=False):
        server, port = self.view.node_parameters()
        logging.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            await self.model.create_community(server, port)
            self.view.button_connect.setEnabled(False)
            self.view.button_register.setEnabled(False)
            self._steps[self._current_step]['next']()
        except (DisconnectedError, ClientError, MalformedDocumentError, ValueError)  as e:
            self.view.display_info(str(e))
        except TimeoutError:
            self.view.display_info(self.tr("Could not connect. Check hostname, ip address or port"))

    @asyncify
    async def check_connect(self, checked=False):
        server, port = self.view.node_parameters()
        logging.debug("Is valid ? ")
        self.view.display_info.setText(self.tr("connecting..."))
        try:
            await self.model.create_community(server, port)
            self.view.button_connect.setEnabled(False)
            self.view.button_register.setEnabled(False)
            registered = await self.model.check_registered()
            self.view.button_connect.setEnabled(True)
            self.view.button_register.setEnabled(True)
            if registered[0] is False and registered[2] is None:
                self.view.display_info(self.tr("Could not find your identity on the network."))
            elif registered[0] is False and registered[2]:
                self.view.display_info(self.tr("""Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
            else:
                self._steps[self._current_step]['next']()
        except (DisconnectedError, ClientError, MalformedDocumentError, ValueError) as e:
            self.view.display_info(str(e))
        except TimeoutError:
            self.view.display_info(self.tr("Could not connect. Check hostname, ip address or port"))
        except NoPeerAvailable:
            self.config_dialog.label_error.setText(self.tr("Could not connect. Check node peering entry"))

    @asyncify
    async def check_register(self, checked=False):
        server, port = self.view.node_parameters()
        logging.debug("Is valid ? ")
        self.view.display_info(self.tr("connecting..."))
        try:
            await self.model.create_community(server, port)
            self.view.button_connect.setEnabled(False)
            self.view.button_register.setEnabled(False)
            registered = await self.model.check_registered()
            self.view.button_connect.setEnabled(True)
            self.view.button_register.setEnabled(True)
            if registered[0] is False and registered[2] is None:
                password = await self.password_asker.async_exec()
                if self.password_asker.result() == QDialog.Rejected:
                    return
                self.view.display_info(self.tr("Broadcasting identity..."))
                result = await self.model.publish_selfcert(password)
                if result[0]:
                    self.view.show_success()
                    QApplication.restoreOverrideCursor()
                    self._steps[self._current_step]['next']()
                else:
                    self.view.show_error(self.model.notification(), result[1])
                QApplication.restoreOverrideCursor()
            elif registered[0] is False and registered[2]:
                self.view.display_info(self.tr("""Your pubkey or UID was already found on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
            else:
                self.display_info("Your account already exists on the network")
        except (DisconnectedError, ClientError, MalformedDocumentError, ValueError) as e:
            self.view.display_info(str(e))
        except NoPeerAvailable:
            self.view.display_info(self.tr("Could not connect. Check node peering entry"))
        except TimeoutError:
            self.view.display_info(self.tr("Could not connect. Check hostname, ip address or port"))

    def show_context_menu(self, point):
        if self.view.stacked_pages.currentWidget() == self.steps[1]['widget']:
            menu = QMenu()
            index = self.model.nodes_tree_model.indexAt(point)
            action = menu.addAction(self.tr("Delete"), self.remove_node)
            action.setData(index.row())
            if len(self.nodes) == 1:
                action.setEnabled(False)
            menu.exec_(QCursor.pos())

    @asyncify
    async def add_node(self, checked=False):
        """
        Add node slot
        """
        server, port = self.view.add_node_parameters()
        try:
            await self.model.add_node(server, port)
        except Exception as e:
            self.view.show_error(self.model.notification(), str(e))

    def remove_node(self):
        """
        Remove node slot
        """
        logging.debug("Remove node")
        index = self.sender().data()
        self.model.remove_node(index)

    def accept(self):
        if self.community not in self.account.communities:
            self.account.add_community(self.community)
        self.view.accept()

    @property
    def view(self) -> CommunityConfigView:
        return self._view

    @property
    def model(self) -> CommunityConfigModel:
        return self._model