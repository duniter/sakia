'''
Created on 2 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.addCommunityDialog_uic import Ui_AddCommunityDialog
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWidgets import QListWidgetItem
from cutecoin.models.community import CommunitiesManager, Community
from cutecoin.models.node import MainNode
import ucoinpy as ucoin

class AddCommunityDialog(QDialog, Ui_AddCommunityDialog):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        super(AddCommunityDialog, self).__init__()
        self.setupUi(self)

    def setCommunitiesManager(self, communitiesManager):
        self.communitiesManager = communitiesManager

    def addCommunity(self):
        '''
        Add community slot
        '''
        server = self.serverEdit.text()
        port = self.portBox.value()
        self.communitiesManager.addCommunity(MainNode(server, port))


