'''
Created on 6 mars 2014

@author: inso
'''
from cutecoin.gen_resources.accountConfigurationDialog_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.configureCommunityDialog import ConfigureCommunityDialog
from cutecoin.models.account.communities.listModel import CommunitiesListModel
from cutecoin.core.exceptions import KeyAlreadyUsed
from cutecoin.models.account import Account
from cutecoin.models.account import Communities
from cutecoin.models.node import Node

from PyQt5.QtWidgets import QDialog, QErrorMessage, QInputDialog

import gnupg
import re


class ConfigureAccountDialog(QDialog, Ui_AccountConfigurationDialog):
    '''
    classdocs
    '''


    def __init__(self, core, account):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(ConfigureAccountDialog, self).__init__()
        self.setupUi(self)
        self.account = account
        self.core = core
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

        text, ok = QInputDialog.getText(self, 'Add a community',
            'Enter a main node address you trust :')

        if ok:
            server, port = text.split(':')[0], int(text.split(':')[1])

            dialog = ConfigureCommunityDialog(self.account, None, Node(server, port))
            dialog.buttonBox.accepted.connect(self.actionAddCommunity)
            dialog.exec_()

    def actionAddCommunity(self):
        self.combo_keysList.setEnabled(False)
        self.combo_keysList.disconnect()
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def actionRemoveCommunity(self):
        for index in self.list_communities.selectedIndexes():
            community = self.account.communities.communitiesList[ index.row() ]
            self.account.wallets.removeAllWalletsOf(community)
            self.account.communities.communitiesList.pop(index.row())

        self.list_communities.setModel( CommunitiesListModel(self.account ))

    def actionEditCommunity(self):
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def openEditCommunityDialog(self, index):
        community = self.account.communities.communitiesList[index.row()]
        dialog = ConfigureCommunityDialog(self.account, community)
        dialog.buttonBox.accepted.connect(self.actionEditCommunity)
        dialog.setAccount(self.account)
        dialog.exec_()

    def keyChanged(self, keyIndex):
        gpg = gnupg.GPG()
        availableKeys = gpg.list_keys(True)
        self.account.keyId = availableKeys[keyIndex]['keyid']

    def accept(self):
        if self.account not in self.core.accounts:
            self.account.name = self.edit_accountName.text()
            try:
                self.core.addAccount(self.account)
            except KeyAlreadyUsed as e:
                QErrorMessage(self).showMessage(e.message)
        self.close()


