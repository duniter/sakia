'''
Created on 8 mars 2014

@author: inso
'''
from cutecoin.gen_resources.communityConfigurationDialog_uic import Ui_CommunityConfigurationDialog
from PyQt5.QtWidgets import QDialog, QErrorMessage, QMenu
from cutecoin.models.community.treeModel import CommunityTreeModel
from cutecoin.models.node import Node
from cutecoin.core.exceptions import NotMemberOfCommunityError

class ConfigureCommunityDialog(QDialog, Ui_CommunityConfigurationDialog):
    '''
    classdocs
    '''


    def __init__(self, account, community, defaultNode=None):
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
                defaultNode.trust = True
                defaultNode.hoster = True
                self.community = self.account.communities.addCommunity(defaultNode, self.account.keyFingerprint())
                self.account.wallets.addWallet(self.community)
                self.communityView.setModel( CommunityTreeModel(self.community) )
                #TODO: Ask for THT pull
            except NotMemberOfCommunityError as e:
                QErrorMessage(self).showMessage(e.message)
        else:
            self.setWindowTitle("Configure community " + self.community.currency)
            #TODO: Ask for THT push
            self.communityView.setModel( CommunityTreeModel(self.community))

    def addNode(self):
        '''
        Add node slot
        '''
        server = self.serverEdit.text()
        port = self.portBox.value()
        if self.community is not None:
            self.community.nodes.append(Node(server, port, trust=True))
            self.communityView.setModel( CommunityTreeModel(self.community ))

    def showContextMenu(self, point):
        menu = QMenu()
        action = menu.addAction("Delete", self.removeNode)
        if self.community is not None:
            if len(self.community.nodes) == 1:
                action.setEnabled(False)
        menu.exec_(self.communityView.mapToGlobal(point))

    def removeNode(self):
        for index in self.communityView.selectedIndexes():
            self.community.nodes.pop(index.row())

        self.communityView.setModel( CommunityTreeModel(self.community ))

    def accept(self):
        #TODO: Ask for THT push
        self.close()




