'''
Created on 2 févr. 2014

@author: inso
'''
from cutecoin.gen_resources.addAccountDialog_uic import Ui_AddAccountDialog
from PyQt5.QtWidgets import QDialog
from cutecoin.gui.addCommunityDialog import AddCommunityDialog
from cutecoin.models.account import Account
from cutecoin.models.account.communities import Communities
from cutecoin.models.account.communities.listModel import CommunitiesListModel

import gnupg


class AddAccountDialog(QDialog, Ui_AddAccountDialog):
    '''
    classdocs
    '''


    def __init__(self, mainWindow):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(AddAccountDialog, self).__init__()
        self.setupUi(self)
        self.dialog = AddCommunityDialog(self)
        self.mainWindow = mainWindow


        self.buttonBox.accepted.connect(self.mainWindow.actionAddAccount)

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

    def actionAddCommunity(self):
        self.communitiesList.setModel(CommunitiesListModel(self.account))


