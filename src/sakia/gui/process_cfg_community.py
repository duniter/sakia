"""
Created on 8 mars 2014

@author: inso
"""

import logging
import asyncio
import aiohttp

from duniterpy.api import errors
from duniterpy.documents import MalformedDocumentError
from PyQt5.QtWidgets import QDialog, QMenu, QApplication
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtSignal, QObject

from ..gen_resources.community_cfg_uic import Ui_CommunityConfigurationDialog
from ..models.peering import PeeringTreeModel
from ..core import Community
from ..core.net import Node
from .widgets import toast
from .widgets.dialogs import QAsyncMessageBox
from ..tools.decorators import asyncify
from ..tools.exceptions import NoPeerAvailable


class Step(QObject):
    def __init__(self, config_dialog, previous_step=None, next_step=None):
        super().__init__()
        self.previous_step = previous_step
        self.next_step = next_step
        self.config_dialog = config_dialog


class StepPageInit(Step):
    """
    First step when adding a community
    """
    def __init__(self, config_dialog):
        super().__init__(config_dialog)
        self.node = None
        logging.debug("Init")
        self.config_dialog.button_connect.clicked.connect(self.check_connect)
        self.config_dialog.button_register.clicked.connect(self.check_register)
        self.config_dialog.button_guest.clicked.connect(self.check_guest)

    @property
    def app(self):
        return self.config_dialog.app

    @property
    def account(self):
        return self.config_dialog.account

    @property
    def community(self):
        return self.config_dialog.community

    @property
    def password_asker(self):
        return self.config_dialog.password_asker

    @asyncify
    async def check_guest(self, checked=False):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        try:
            self.node = await Node.from_address(None, server, port, session=aiohttp.ClientSession())
            community = Community.create(self.node)
            self.config_dialog.button_connect.setEnabled(False)
            self.config_dialog.button_register.setEnabled(False)
            self.config_dialog.community = community
            self.config_dialog.next()
        except aiohttp.errors.DisconnectedError as e:
            self.config_dialog.label_error.setText(str(e))
        except aiohttp.errors.ClientError as e:
            self.config_dialog.label_error.setText(str(e))
        #except (MalformedDocumentError, ValueError) as e:
        #    self.config_dialog.label_error.setText(str(e))

    @asyncify
    async def check_connect(self, checked=False):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        try:
            self.node = await Node.from_address(None, server, port, session=aiohttp.ClientSession())
            community = Community.create(self.node)
            self.config_dialog.button_connect.setEnabled(False)
            self.config_dialog.button_register.setEnabled(False)
            registered = await self.account.check_registered(community)
            self.config_dialog.button_connect.setEnabled(True)
            self.config_dialog.button_register.setEnabled(True)
            if registered[0] is False and registered[2] is None:
                self.config_dialog.label_error.setText(self.tr("Could not find your identity on the network."))
            elif registered[0] is False and registered[2]:
                self.config_dialog.label_error.setText(self.tr("""Your pubkey or UID is different on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
            else:
                self.config_dialog.community = community
                self.config_dialog.next()
        except aiohttp.errors.DisconnectedError as e:
            self.config_dialog.label_error.setText(str(e))
        except aiohttp.errors.ClientError as e:
            self.config_dialog.label_error.setText(str(e))
        except (MalformedDocumentError, ValueError) as e:
            self.config_dialog.label_error.setText(str(e))
        except NoPeerAvailable:
            self.config_dialog.label_error.setText(self.tr("Could not connect. Check node peering entry"))

    @asyncify
    async def check_register(self, checked=False):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        try:
            session = aiohttp.ClientSession()
            self.node = await Node.from_address(None, server, port, session=session)
            community = Community.create(self.node)
            self.config_dialog.button_connect.setEnabled(False)
            self.config_dialog.button_register.setEnabled(False)
            registered = await self.account.check_registered(community)
            self.config_dialog.button_connect.setEnabled(True)
            self.config_dialog.button_register.setEnabled(True)
            if registered[0] is False and registered[2] is None:
                password = await self.password_asker.async_exec()
                if self.password_asker.result() == QDialog.Rejected:
                    return
                self.config_dialog.label_error.setText(self.tr("Broadcasting identity..."))
                result = await self.account.send_selfcert(password, community)
                if result[0]:
                    if self.app.preferences['notifications']:
                        toast.display(self.tr("UID broadcast"), self.tr("Identity broadcasted to the network"))
                    QApplication.restoreOverrideCursor()
                    self.config_dialog.next()
                else:
                    self.config_dialog.label_error.setText(self.tr("Error") + " " + \
                                                           self.tr("{0}".format(result[1])))
                    if self.app.preferences['notifications']:
                        toast.display(self.tr("Error"), self.tr("{0}".format(result[1])))
                QApplication.restoreOverrideCursor()
                self.config_dialog.community = community
            elif registered[0] is False and registered[2]:
                self.config_dialog.label_error.setText(self.tr("""Your pubkey or UID was already found on the network.
Yours : {0}, the network : {1}""".format(registered[1], registered[2])))
            else:
                self.config_dialog.label_error.setText(self.tr("Your account already exists on the network"))
        except (MalformedDocumentError, ValueError, errors.duniterError,
                aiohttp.errors.ClientError, aiohttp.errors.DisconnectedError) as e:
            session.close()
            self.config_dialog.label_error.setText(str(e))
        except NoPeerAvailable:
            self.config_dialog.label_error.setText(self.tr("Could not connect. Check node peering entry"))

    def is_valid(self):
        return self.node is not None

    def process_next(self):
        """
        We create the community
        """
        account = self.config_dialog.account
        logging.debug("Account : {0}".format(account))
        self.config_dialog.community = Community.create(self.node)

    def display_page(self):
        self.config_dialog.button_next.hide()
        self.config_dialog.button_previous.hide()


class StepPageAddpeers(Step):
    """
    The step where the user add peers
    """
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        return True

    def process_next(self):
        pass

    def display_page(self):
        self.config_dialog.button_next.show()
        self.config_dialog.button_previous.show()
        # We add already known peers to the displayed list
        self.config_dialog.nodes = self.config_dialog.community.network.root_nodes
        tree_model = PeeringTreeModel(self.config_dialog.community)

        self.config_dialog.tree_peers.setModel(tree_model)
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText(self.config_dialog.tr("Ok"))


class ProcessConfigureCommunity(QDialog, Ui_CommunityConfigurationDialog):
    """
    Dialog to configure or add a community
    """
    community_added = pyqtSignal()

    def __init__(self, app, account, community, password_asker):
        """
        Constructor

        :param sakia.core.Application app: The application
        :param sakia.core.Account account: The configured account
        :param sakia.core.Community community: The configured community
        :param sakia.gui.password_asker.Password_Asker password_asker: The password asker
        """
        super().__init__()
        self.setupUi(self)
        self.app = app
        self.community = community
        self.account = account
        self.password_asker = password_asker
        self.step = None
        self.nodes = []

        self.community_added.connect(self.add_community_and_close)
        self._step_init = StepPageInit(self)
        step_add_peers = StepPageAddpeers(self)

        self._step_init.next_step = step_add_peers

        if self.community is not None:
            self.stacked_pages.removeWidget(self.page_node)
            self.step = step_add_peers
            self.setWindowTitle(self.tr("Configure community {0}").format(self.community.currency))
        else:
            self.step = self._step_init
            self.setWindowTitle(self.tr("Add a community"))

        self.step.display_page()

    def next(self):
        if self.step.next_step is not None:
            if self.step.is_valid():
                self.step.process_next()
                self.step = self.step.next_step
                next_index = self.stacked_pages.currentIndex() + 1
                self.stacked_pages.setCurrentIndex(next_index)
                self.step.display_page()
        else:
            self.add_community_and_close()

    def previous(self):
        if self.step.previous_step is not None:
            self.step = self.step.previous_step
            previous_index = self.stacked_pages.currentIndex() - 1
            self.stacked_pages.setCurrentIndex(previous_index)
            self.step.display_page()

    async def start_add_node(self):
        """
        Add node slot
        """
        server = self.lineedit_add_address.text()
        port = self.spinbox_add_port.value()

        try:
            node = await Node.from_address(self.community.currency, server, port, session=self.community.network.session)
            self.community.add_node(node)
        except Exception as e:
            await QAsyncMessageBox.critical(self, self.tr("Error"),
                                 str(e))
        self.tree_peers.setModel(PeeringTreeModel(self.community))

    def add_node(self):
        asyncio.ensure_future(self.start_add_node())

    def remove_node(self):
        """
        Remove node slot
        """
        logging.debug("Remove node")
        index = self.sender().data()
        self.community.remove_node(index)
        self.tree_peers.setModel(PeeringTreeModel(self.community))

    @property
    def nb_steps(self):
        s = self.step
        nb_steps = 1
        while s.next_step != None:
            s = s.next_step
            nb_steps = nb_steps + 1
        return nb_steps

    def showContextMenu(self, point):
        if self.stacked_pages.currentIndex() == self.nb_steps - 1:
            menu = QMenu()
            index = self.tree_peers.indexAt(point)
            action = menu.addAction(self.tr("Delete"), self.remove_node)
            action.setData(index.row())
            if self.community is not None:
                if len(self.nodes) == 1:
                    action.setEnabled(False)
            menu.exec_(QCursor.pos())

    def async_exec(self):
        future = asyncio.Future()
        self.finished.connect(lambda r: future.set_result(r))
        self.open()
        return future

    def add_community_and_close(self):
        if self.community not in self.account.communities:
            self.account.add_community(self.community)
        self.accept()
