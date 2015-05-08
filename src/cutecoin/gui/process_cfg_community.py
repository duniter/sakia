'''
Created on 8 mars 2014

@author: inso
'''

import logging
import requests

from ucoinpy.api import bma
from ucoinpy.api.bma import ConnectionHandler
from ucoinpy.documents.peer import Peer

from PyQt5.QtWidgets import QDialog, QMenu, QMessageBox
from PyQt5.QtGui import QCursor

from ..gen_resources.community_cfg_uic import Ui_CommunityConfigurationDialog
from ..models.peering import PeeringTreeModel
from ..core.community import Community
from ..core.person import Person
from ..core.net.node import Node
from ..tools.exceptions import PersonNotFoundError, NoPeerAvailable


class Step():
    def __init__(self, config_dialog, previous_step=None, next_step=None):
        self.previous_step = previous_step
        self.next_step = next_step
        self.config_dialog = config_dialog


class StepPageInit(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)
        self.node = None
        logging.debug("Init")

    def is_valid(self):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        try:
            self.node = Node.from_address(None, server, port)
        except Exception as e:
            QMessageBox.critical(self.config_dialog, ":(",
                        str(e),
                        QMessageBox.Ok)

        return True

    def process_next(self):
        '''
        We create the community
        '''
        account = self.config_dialog.account
        logging.debug("Account : {0}".format(account))
        self.config_dialog.community = Community.create(self.node)

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)


class StepPageAddpeers(Step):
    '''
    The step where the user add peers
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        return True

    def process_next(self):
        pass

    def display_page(self):
        # We add already known peers to the displayed list
        self.config_dialog.nodes = self.config_dialog.community.network.root_nodes
        try:
            tree_model = PeeringTreeModel(self.config_dialog.community)
        except requests.exceptions.RequestException:
            raise

        self.config_dialog.tree_peers.setModel(tree_model)
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText(self.config_dialog.tr("Ok"))


class ProcessConfigureCommunity(QDialog, Ui_CommunityConfigurationDialog):
    '''
    Dialog to configure or add a community
    '''

    def __init__(self, account, community, password_asker, default_node=None):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.community = community
        self.account = account
        self.password_asker = password_asker
        self.step = None
        self.nodes = []

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
                try:
                    self.step.process_next()
                    self.step = self.step.next_step
                    next_index = self.stacked_pages.currentIndex() + 1
                    self.stacked_pages.setCurrentIndex(next_index)
                    self.step.display_page()
                except NoPeerAvailable:
                    return
                except requests.exceptions.RequestException as e:
                    QMessageBox.critical(self.config_dialog, ":(",
                                str(e),
                                QMessageBox.Ok)
                    return
        else:
            self.accept()

    def previous(self):
        if self.step.previous_step is not None:
            self.step = self.step.previous_step
            previous_index = self.stacked_pages.currentIndex() - 1
            self.stacked_pages.setCurrentIndex(previous_index)
            self.step.display_page()

    def add_node(self):
        '''
        Add node slot
        '''
        server = self.lineedit_add_address.text()
        port = self.spinbox_add_port.value()

        try:
            node = Node.from_address(self.community.currency, server, port)
            self.community.add_node(node)
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"),
                                 str(e))
        self.tree_peers.setModel(PeeringTreeModel(self.community))

    def remove_node(self):
        '''
        Remove node slot
        '''
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

    def accept(self):
        try:
            Person.lookup(self.account.pubkey, self.community, cached=False)
        except PersonNotFoundError as e:
            reply = QMessageBox.question(self, self.tr("Pubkey not found"),
                                 self.tr("""The public key of your account wasn't found in the community. :\n
{0}\n
Would you like to publish the key ?""").format(self.account.pubkey))
            if reply == QMessageBox.Yes:
                password = self.password_asker.exec_()
                if self.password_asker.result() == QDialog.Rejected:
                    return
                try:
                    self.account.send_selfcert(password, self.community)
                except ValueError as e:
                    QMessageBox.critical(self, self.tr("Pubkey publishing error"),
                                      e.message)
                except NoPeerAvailable as e:
                    QMessageBox.critical(self, self.tr("Network error"),
                                         self.tr("Couldn't connect to network : {0}").format(e),
                                         QMessageBox.Ok)
                except Exception as e:
                    QMessageBox.critical(self, self.tr("Error"),
                                         "{0}".format(e),
                                         QMessageBox.Ok)

        if self.community not in self.account.communities:
            self.account.add_community(self.community)
        super().accept()
