"""
Created on 8 mars 2014

@author: inso
"""

import logging
import asyncio

from PyQt5.QtWidgets import QDialog, QMenu, QMessageBox, QApplication
from PyQt5.QtGui import QCursor
from PyQt5.QtCore import pyqtSlot, pyqtSignal, QObject

from ..gen_resources.community_cfg_uic import Ui_CommunityConfigurationDialog
from ..models.peering import PeeringTreeModel
from ..core import Community
from ..core.registry.identity import BlockchainState
from ..core.net import Node
from . import toast


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

    @asyncio.coroutine
    def coroutine_check_connect(self):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        self.node = yield from Node.from_address(self.config_dialog.app.network_manager, None, server, port)
        if self.node:
            identity = yield from self.app.identities_registry.future_find(self.account.pubkey, self.community)
            if identity.blockchain_state == BlockchainState.NOT_FOUND:
                self.config_dialog.label_error.setText(self.tr("Could not find your identity on the network."))
        else:
            self.next()

    @pyqtSlot()
    def check_connect(self):
        logging.debug("Check node")
        asyncio.async(self.coroutine_check_connect())

    @asyncio.coroutine
    def coroutine_check_register(self):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        self.node = yield from Node.from_address(self.config_dialog.app.network_manager, None, server, port)
        if self.node:
            community = Community.create(self.app.network_manager, self.node)
            identity = yield from self.app.identities_registry.future_find(self.account.pubkey, community)
            if identity.blockchain_state == BlockchainState.NOT_FOUND:
                password = yield from self.password_asker.future_exec()
                if self.password_asker.result() == QDialog.Rejected:
                    return
                self.config_dialog.label_error.setText(self.tr("Broadcasting identity..."))
                self.account.selfcert_broadcasted.connect(self.handle_broadcast)
                self.account.broadcast_error.connect(self.handle_error)
                yield from self.account.send_selfcert(password, community)
                self.config_dialog.community = community
        else:
            self.config_dialog.label_error.setText(self.tr("Could not connect."))

    @pyqtSlot()
    def check_register(self):
        logging.debug("Check node")
        asyncio.async(self.coroutine_check_register())

    @pyqtSlot(int, str)
    def handle_broadcast(self):
        if self.app.preferences['notifications']:
            toast.display(self.tr("UID broadcast"), self.tr("Identity broadcasted to the network"))
        # Disabled : https://github.com/harvimt/quamash/issues/41
        # else:
        #    QMessageBox.information(self, self.tr("UID broadcast"), self.tr("Identity broadcasted to the network"))
        self.account.selfcert_broadcasted.disconnect()
        self.account.broadcast_error.disconnect(self.handle_error)
        QApplication.restoreOverrideCursor()
        self.config_dialog.next()

    @pyqtSlot(int, str)
    def handle_error(self, error_code, text):
        self.config_dialog.label_error.setText(self.tr("Error") + " " + \
                                               self.tr("{0} : {1}".format(error_code, text)))
        if self.app.preferences['notifications']:
            toast.display(self.tr("Error"), self.tr("{0} : {1}".format(error_code, text)))
        # Disabled : https://github.com/harvimt/quamash/issues/41
        #  else:
        #    QMessageBox.critical(self, self.tr("Error"), self.tr("{0} : {1}".format(error_code, text)))
        self.account.selfcert_broadcasted.disconnect()
        self.account.broadcast_error.disconnect(self.handle_error)
        QApplication.restoreOverrideCursor()

    def is_valid(self):
        return self.node is not None

    def process_next(self):
        """
        We create the community
        """
        account = self.config_dialog.account
        logging.debug("Account : {0}".format(account))
        self.config_dialog.community = Community.create(self.config_dialog.app.network_manager, self.node)

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

        :param cutecoin.core.Application app: The application
        :param cutecoin.core.Account account: The configured account
        :param cutecoin.core.Community community: The configured community
        :param cutecoin.gui.password_asker.Password_Asker password_asker: The password asker
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
        step_init = StepPageInit(self)
        step_add_peers = StepPageAddpeers(self)

        step_init.next_step = step_add_peers

        if self.community is not None:
            self.stacked_pages.removeWidget(self.page_init)
            self.step = step_add_peers
            self.setWindowTitle(self.tr("Configure community {0}").format(self.community.currency))
        else:
            self.step = step_init
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

    @asyncio.coroutine
    def start_add_node(self):
        """
        Add node slot
        """
        server = self.lineedit_add_address.text()
        port = self.spinbox_add_port.value()

        try:
            node = yield from Node.from_address(self.app.network_manager, self.community.currency, server, port)
            self.community.add_node(node)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 str(e))
        self.tree_peers.setModel(PeeringTreeModel(self.community))

    def add_node(self):
        asyncio.async(self.start_add_node())

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

    def add_community_and_close(self):
        if self.community not in self.account.communities:
            self.account.add_community(self.community)
        self.accept()

