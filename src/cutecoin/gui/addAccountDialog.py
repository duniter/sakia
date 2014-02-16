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
        self.mainWindow = mainWindow

        self.buttonBox.accepted.connect(self.mainWindow.actionAddAccount)

        self.setData()

    def setData(self):
        gpg = gnupg.GPG()
        self.pgpKeysList.clear()
        availableKeys = gpg.list_keys(True)
        for key in availableKeys:
            self.pgpKeysList.addItem(key['uids'][0])

        self.account = Account.create(availableKeys[0]['keyid'], "", Communities())
        self.pgpKeysList.setEnabled(True)
        self.pgpKeysList.currentIndexChanged[int].connect(self.keyChanged)
        self.communityDialog = AddCommunityDialog(self)

    def openAddCommunityDialog(self):
        self.communityDialog.setAccount(self.account)
        self.communityDialog.exec_()

    def actionAddCommunity(self):
        self.pgpKeysList.setEnabled(False)
        self.pgpKeysList.disconnect()
        self.communitiesList.setModel(CommunitiesListModel(self.account))

    def keyChanged(self, keyIndex):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys(True)
        self.account.pgpKeyId = availableKeys[keyIndex]['keyid']

