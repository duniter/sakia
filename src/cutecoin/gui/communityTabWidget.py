'''
Created on 2 févr. 2014

@author: inso
'''
from PyQt5.QtWidgets import QWidget
from cutecoin.models.community.membersListModel import MembersListModel
from cutecoin.models.transaction.issuancesListModel import IssuancesListModel
from cutecoin.gen_resources.communityTabWidget_uic import Ui_CommunityTabWidget

class CommunityTabWidget(QWidget, Ui_CommunityTabWidget):
    '''
    classdocs
    '''
    def __init__(self, account, community):
        '''
        Constructor
        '''
        super(CommunityTabWidget, self).__init__()
        self.setupUi(self)
        self.community = community
        self.communityMembersList.setModel(MembersListModel(community))
        self.issuancesList.setModel(IssuancesListModel(account, community))



