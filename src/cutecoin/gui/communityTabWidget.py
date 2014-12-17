'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget, QErrorMessage
from cutecoin.models.members import MembersListModel
from cutecoin.gen_resources.communityTabWidget_uic import Ui_CommunityTabWidget


class CommunityTabWidget(QWidget, Ui_CommunityTabWidget):

    '''
    classdocs
    '''

    def __init__(self, account, community):
        '''
        Constructor
        '''
        super().__init__()
        self.setupUi(self)
        self.community = community
        self.account = account
        self.list_community_members.setModel(MembersListModel(community))
        if self.account.member_of(self.community):
            self.button_membership.setText("Send leaving demand")
            self.button_membership.clicked.connect(self.send_membership_leaving)
        else:
            self.button_membership.setText("Send membership demand")
            self.button_membership.clicked.connect(self.send_membership_demand)

    def send_membership_demand(self):
        result = self.account.send_membership_in(self.community)
        if (result):
            QErrorMessage(self).showMessage(result)

    def send_membership_leaving(self):
        result = self.account.send_membership_out(self.community)
        if (result):
            QErrorMessage(self).showMessage(result)
