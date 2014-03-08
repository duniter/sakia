'''
Created on 6 mars 2014

@author: inso
'''
from cutecoin.gen_resources.accountConfigurationDialog_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.configureCommunityDialog import ConfigureCommunityDialog
from cutecoin.models.account.communities.listModel import CommunitiesListModel
from PyQt5.QtWidgets import QDialog
from cutecoin.models.account import Account
from cutecoin.models.account import Communities
import gnupg


class ConfigureAccountDialog(QDialog, Ui_AccountConfigurationDialog):
    '''
    classdocs
    '''


    def __init__(self, account):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(ConfigureAccountDialog, self).__init__()
        self.setupUi(self)
        self.account = account
        if self.account is None:
            self.setWindowTitle("New account")
        else:
            self.setWindowTitle("Configure " + self.account.name)
            self.combo_keysList.setEnabled(False)

        self.setData()

    def setData(self):
        gpg = gnupg.GPG()
        self.combo_keysList.clear()
        availableKeys = gpg.list_keys(True)

        if self.account is None:
            self.account = Account.create(availableKeys[0]['keyid'], "", Communities())
            self.combo_keysList.currentIndexChanged[int].connect(self.keyChanged)

        for index, key in enumerate(availableKeys):
            self.combo_keysList.addItem(key['uids'][0])
            if (key['keyid']) == self.account.keyId:
                self.combo_keysList.setCurrentIndex(index)


        self.list_communities.setModel(CommunitiesListModel(self.account))
        self.edit_accountName.setText(self.account.name)

    def openAddCommunityDialog(self):
        dialog = ConfigureCommunityDialog(None)
        dialog.setWindowTitle("Add a community")
        dialog.buttonBox.accepted.connect(self.actionAddCommunity)
        dialog.setAccount(self.account)
        dialog.exec_()

    def actionAddCommunity(self):
        self.combo_keysList.setEnabled(False)
        self.combo_keysList.disconnect()
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def actionRemoveCommunity(self):
        #TODO:Remove selected community
        pass

    def actionEditCommunity(self):
        #TODO: Edit selected community
        pass

    def keyChanged(self, keyIndex):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys(True)
        self.account.keyId = availableKeys[keyIndex]['keyid']

