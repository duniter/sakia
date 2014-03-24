'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget
from cutecoin.models.community.membersListModel import MembersListModel
from cutecoin.models.transaction.issuancesListModel import IssuancesListModel
from cutecoin.gui.issuanceDialog import IssuanceDialog
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
        self.account = account
        #TODO: Rename to list:
        self.list_community_members.setModel(MembersListModel(community))
        self.list_issuances.setModel(IssuancesListModel(account, community))
        if self.account.issued_last_dividend(community):
            self.button_issuance.setEnabled(False)
        else:
            self.button_issuance.setEnabled(True)

    def open_issuance_dialog(self):
        logging.debug("Display dialog")
        dialog = IssuanceDialog(self.account, self.community)
        dialog.exec_()
