'''
Created on 8 mars 2014

@author: inso
'''
from cutecoin.gen_resources.communityConfigurationDialog_uic import Ui_CommunityConfigurationDialog
from PyQt5.QtWidgets import QDialog, QErrorMessage
from cutecoin.models.community.treeModel import CommunityTreeModel
from cutecoin.models.node import TrustedNode
from cutecoin.core.exceptions import NotMemberOfCommunityError

class ConfigureCommunityDialog(QDialog, Ui_CommunityConfigurationDialog):
    '''
    classdocs
    '''


    def __init__(self, community):
        '''
        Constructor
        '''
        super(ConfigureCommunityDialog, self).__init__()
        self.setupUi(self)
        self.community = community
        if self.community is None:
            self.setWindowTitle("Add a community")
        else:
            self.setWindowTitle("Configure community " + self.community.currency)
        self.setData()

    def setData(self):
        if self.community is not None:
            self.communityView.setModel( CommunityTreeModel(self.community))

    def setAccount(self, account):
        self.account = account

    def addNode(self):
        '''
        Add node slot
        '''
        server = self.serverEdit.text()
        port = self.portBox.value()
        if self.community == None:
            try:
                self.community = self.account.communities.addCommunity(TrustedNode(server, port), self.account.keyFingerprint())
                self.account.wallets.addWallet(self.community)
                self.communityView.setModel( CommunityTreeModel(self.community) )
            except NotMemberOfCommunityError as e:
                QErrorMessage(self).showMessage(e.message)
        else:
            self.community.addTrustedNode( TrustedNode(server, port ))
            self.communityView.setModel( CommunityTreeModel(self.community ))

    def accept(self):
        self.close()



