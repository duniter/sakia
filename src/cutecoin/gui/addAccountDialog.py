'''
Created on 2 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.addAccountDialog_uic import Ui_AddAccountDialog
from PyQt5.QtWidgets import QDialog
from cutecoin.gui.addCommunityDialog import AddCommunityDialog
from cutecoin.models.account import Account
from cutecoin.models.account.communities import Communities
from cutecoin.models.account.communities.treeModel import CommunitiesTreeModel

import gnupg


class AddAccountDialog(QDialog, Ui_AddAccountDialog):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(AddAccountDialog, self).__init__()
        self.setupUi(self)
        self.dialog = AddCommunityDialog(self)
        self.setData()

    def setData(self):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys(True)
        for key in availableKeys:
            self.pgpkeyList.addItem(key['uids'][0])


        self.account = Account(self.pgpkeyList.currentText(), "", Communities())

    def openAddCommunityDialog(self):
        self.dialog.setCommunities(self.account.communities)
        self.dialog.exec_()

    def validAddCommunityDialog(self):
        self.communitiesTable.setModel(CommunitiesTreeModel(self.account))


