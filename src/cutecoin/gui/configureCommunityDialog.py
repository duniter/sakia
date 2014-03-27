'''
Created on 8 mars 2014

@author: inso
'''
import logging
from cutecoin.gen_resources.communityConfigurationDialog_uic import Ui_CommunityConfigurationDialog
from PyQt5.QtWidgets import QDialog, QErrorMessage, QMenu, QMessageBox
from cutecoin.models.community.treeModel import CommunityTreeModel
from cutecoin.models.node import Node
from cutecoin.core.exceptions import NotMemberOfCommunityError


class ConfigureCommunityDialog(QDialog, Ui_CommunityConfigurationDialog):

    '''
    classdocs
    '''

    def __init__(self, account, community, default_node=None):
        '''
        Constructor
        '''
        super(ConfigureCommunityDialog, self).__init__()
        self.setupUi(self)
        self.community = community
        self.account = account
        if self.community is None:
            self.setWindowTitle("Add a community")
            try:
                default_node.trust = True
                default_node.hoster = True
                self.community = self.account.communities.add_community(
                    default_node)
                self.account.wallets.add_wallet(self.community)
                self.tree_nodes.setModel(CommunityTreeModel(self.community))
                # TODO: Ask for THT pull
                msg_box = QMessageBox()
                msg_box.setText("Add a community")
                msg_box.setInformativeText(
                    "Would you like to existing THT from this community ?")
                msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg_box.exec_()
                if msg_box.clickedButton() == QMessageBox.Yes:
                    self.account.pull_tht(self.community)
            except NotMemberOfCommunityError as e:
                QErrorMessage(self).showMessage(e.message)
        else:
            self.setWindowTitle(
                "Configure community " +
                self.community.currency)
            self.tree_nodes.setModel(CommunityTreeModel(self.community))

    def add_node(self):
        '''
        Add node slot
        '''
        server = self.edit_server.text()
        port = self.box_port.value()
        if self.community is not None:
            self.community.nodes.append(Node(server, port, trust=True))
            self.tree_nodes.setModel(CommunityTreeModel(self.community))

    def showContextMenu(self, point):
        menu = QMenu()
        action = menu.addAction("Delete", self.removeNode)
        if self.community is not None:
            if len(self.community.nodes) == 1:
                action.setEnabled(False)
        menu.exec_(self.tree_nodes.mapToGlobal(point))

    def remove_node(self):
        for index in self.tree_nodes.selectedIndexes():
            self.community.nodes.pop(index.row())

        self.tree_nodes.setModel(CommunityTreeModel(self.community))

    def accept(self):
        reply = QMessageBox.question(
            self,
            "Trusts and hosters changed",
            "Would you like to push THT to the community ?",
            QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            logging.debug("Yes clicked")
            self.account.push_tht(self.community)

        self.close()
