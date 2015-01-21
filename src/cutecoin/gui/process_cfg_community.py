'''
Created on 8 mars 2014

@author: inso
'''

import logging
from ucoinpy.api import bma
from ucoinpy.api.bma import ConnectionHandler
from ucoinpy.documents.peer import Peer

from PyQt5.QtWidgets import QDialog, QMenu, QMessageBox

from ..gen_resources.community_cfg_uic import Ui_CommunityConfigurationDialog
from ..models.peering import PeeringTreeModel
from ..core.community import Community
from ..core.person import Person
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
        logging.debug("Init")

    def is_valid(self):
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        logging.debug("Is valid ? ")
        try:
            peer_data = bma.network.Peering(ConnectionHandler(server, port))
            peer_data.get()['raw']
        except:
            QMessageBox.critical(self.config_dialog, "Server error",
                              "Cannot get node peering")
            return False
        return True

    def process_next(self):
        '''
        We create the community
        '''
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        account = self.config_dialog.account
        logging.debug("Account : {0}".format(account))
        try:
            peering = bma.network.Peering(ConnectionHandler(server, port))
            peer_data = peering.get()
            peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                          peer_data['signature']))
            currency = peer.currency
            self.config_dialog.community = Community.create(currency, peer)
        except NoPeerAvailable:
            QMessageBox.critical(self.config_dialog, "Server Error",
                              "Cannot join any peer in this community.")
            raise

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
        for peer in self.config_dialog.community.peers:
            self.config_dialog.peers.append(peer)
        tree_model = PeeringTreeModel(self.config_dialog.community)
        self.config_dialog.tree_peers.setModel(tree_model)
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText("Ok")


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
        self.peers = []

        step_init = StepPageInit(self)
        step_add_peers = StepPageAddpeers(self)

        step_init.next_step = step_add_peers

        if self.community is not None:
            self.stacked_pages.removeWidget(self.page_init)
            self.step = step_add_peers
            self.setWindowTitle("Configure community "
                                + self.community.currency)
        else:
            self.step = step_init
            self.setWindowTitle("Add a community")

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
        server = self.lineedit_server.text()
        port = self.spinbox_port.value()
        try:
            peer_data = bma.network.Peering(ConnectionHandler(server, port))

            peer = Peer.from_signed_raw("{0}{1}\n".format(peer_data['raw'],
                                                      peer_data['signature']))
            self.community.peers.append(peer)
        except:
            QMessageBox.critical(self, "Server error",
                              "Cannot get node peering")
        self.tree_peers.setModel(PeeringTreeModel(self.community))

    def showContextMenu(self, point):
        if self.stacked_pages.currentIndex() == 1:
            menu = QMenu()
            action = menu.addAction("Delete", self.removeNode)
            if self.community is not None:
                if len(self.peers) == 1:
                    action.setEnabled(False)
            menu.exec_(self.mapToGlobal(point))

    def accept(self):
        try:
            Person.lookup(self.account.pubkey, self.community, cached=False)
        except PersonNotFoundError as e:
            reply = QMessageBox.question(self, "Pubkey not found",
                                 "The public key of your account wasn't found in the community. :\n \
                                 {0}\n \
                                 Would you like to publish the key ?".format(self.account.pubkey))
            if reply == QMessageBox.Yes:
                password = self.password_asker.ask()
                if password == "":
                    return
                try:
                    self.account.send_pubkey(password, self.community)
                except ValueError as e:
                    QMessageBox.critical(self, "Pubkey publishing error",
                                      e.message)
            else:
                return

        if self.community not in self.account.communities:
            self.account.add_community(self.community)
        self.accepted.emit()
        self.close()
