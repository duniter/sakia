'''
Created on 6 mars 2014

@author: inso
'''
from cutecoin.gen_resources.accountConfigurationDialog_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.processConfigureCommunity import ProcessConfigureCommunity
from cutecoin.models.account.communities.listModel import CommunitiesListModel
from cutecoin.tools.exceptions import KeyAlreadyUsed
from cutecoin.models.account import Account
from cutecoin.models.account import Communities
from cutecoin.models.node import Node

from PyQt5.QtWidgets import QDialog, QErrorMessage, QInputDialog

import gnupg


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
            self.combo_keys_list.setEnabled(False)

        self.set_data()

    def set_data(self):
        gpg = gnupg.GPG()
        self.combo_keys_list.clear()
        available_keys = gpg.list_keys(True)

        if self.account is None:
            self.account = Account.create(
                available_keys[0]['keyid'],
                "",
                Communities())
            self.combo_keys_list.currentIndexChanged[
                int].connect(self.key_changed)

        for index, key in enumerate(available_keys):
            self.combo_keys_list.addItem(key['uids'][0])
            if (key['keyid']) == self.account.keyid:
                self.combo_keys_list.setCurrentIndex(index)

        self.list_communities.setModel(CommunitiesListModel(self.account))
        self.edit_account_name.setText(self.account.name)

    def open_process_add_community(self):
            dialog = ProcessConfigureCommunity(self.account, None)
            dialog.exec_()

    def action_add_community(self):
        self.combo_keys_list.setEnabled(False)
        self.combo_keys_list.disconnect()
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def action_remove_community(self):
        for index in self.list_communities.selectedIndexes():
            community = self.account.communities.communitiesList[index.row()]
            self.account.wallets.removeAllWalletsOf(community)
            self.account.communities.communitiesList.pop(index.row())

        self.list_communities.setModel(CommunitiesListModel(self.account))

    def action_edit_community(self):
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def open_process_edit_community(self, index):
        community = self.account.communities.communities_list[index.row()]
        dialog = ProcessConfigureCommunity(self.account, community)
        dialog.button_box.accepted.connect(self.action_edit_community)
        dialog.exec_()

    def key_changed(self, key_index):
        gpg = gnupg.GPG()
        available_keys = gpg.list_keys(True)
        self.account.keyid = available_keys[key_index]['keyid']

    def accept(self):
        if self.account not in self.core.accounts:
            self.account.name = self.edit_account_name.text()
            try:
                self.core.add_account(self.account)
            except KeyAlreadyUsed as e:
                QErrorMessage(self).showMessage(e.message)
        self.close()
