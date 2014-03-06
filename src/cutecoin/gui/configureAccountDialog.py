'''
Created on 6 mars 2014

@author: inso
'''
from cutecoin.gen_resources.accountConfigurationDialog_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.addCommunityDialog import AddCommunityDialog
from cutecoin.models.account import Account
from cutecoin.models.account.communities import Communities
from cutecoin.models.account.communities.listModel import CommunitiesListModel
from PyQt5.QtWidgets import QDialog

import gnupg


class ConfigureAccountDialog(QDialog, Ui_AccountConfigurationDialog):
    '''
    classdocs
    '''


    def __init__(self, mainWindow):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(ConfigureAccountDialog, self).__init__()
        self.setupUi(self)
        self.account = mainWindow.core.currentAccount
        self.setWindowTitle("Configure " + self.account.name)
        self.setData()

    def setData(self):
        gpg = gnupg.GPG()
        self.combo_keysList.clear()
        availableKeys = gpg.list_keys(True)
        for index, key in enumerate(availableKeys):
            self.combo_keysList.addItem(key['uids'][0])
            if (key['keyid']) == self.account.keyId:
                self.combo_keysList.setCurrentIndex(index)
        self.combo_keysList.setEnabled(False)

        self.list_communities.setModel(CommunitiesListModel(self.account))
        self.edit_accountName.setText(self.account.name)

    def openAddCommunityDialog(self):
        dialog = AddCommunityDialog(self)
        dialog.setAccount(self.account)
        dialog.exec_()

    def actionAddCommunity(self):
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def actionRemoveCommunity(self):
        #TODO:Remove selected community
        pass

    def actionEditCommunity(self):
        #TODO: Edit selected community
        pass


