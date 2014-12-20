'''
Created on 2 févr. 2014

@author: inso
'''

import logging
from PyQt5.QtWidgets import QWidget, QErrorMessage
from cutecoin.models.members import MembersListModel
from cutecoin.gen_resources.communityTabWidget_uic import Ui_CommunityTabWidget
from cutecoin.gui.addContactDialog import AddContactDialog
from cutecoin.wot.qt.form import Form


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
        self.list_community_members.doubleClicked.connect(self.add_member_as_contact)
        if self.account.member_of(self.community):
            self.button_membership.setText("Send leaving demand")
            self.button_membership.clicked.connect(self.send_membership_leaving)
        else:
            self.button_membership.setText("Send membership demand")
            self.button_membership.clicked.connect(self.send_membership_demand)

        # create wot widget
        self.verticalLayout_2.addWidget(Form(account, community))

    def add_member_as_contact(self, index):
        members_model = self.list_community_members.model()
        members = members_model.members
        logging.debug("Members : {0}".format(len(members)))
        if index.row() < len(members):
            dialog = AddContactDialog(self.account, self)
            person = members[index.row()]
            dialog.edit_name.setText(person.name)
            dialog.edit_pubkey.setText(person.pubkey)
            dialog.exec_()


    def send_membership_demand(self):
        result = self.account.send_membership_in(self.community)
        if (result):
            QErrorMessage(self).showMessage(result)

    def send_membership_leaving(self):
        result = self.account.send_membership_out(self.community)
        if (result):
            QErrorMessage(self).showMessage(result)
