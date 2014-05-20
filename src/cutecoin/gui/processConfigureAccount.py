'''
Created on 6 mars 2014

@author: inso
'''
from cutecoin.gen_resources.accountConfigurationDialog_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.processConfigureCommunity import ProcessConfigureCommunity
from cutecoin.models.account.communities.listModel import CommunitiesListModel
from cutecoin.tools.exceptions import KeyAlreadyUsed
from cutecoin.models.account import Account
from cutecoin.models.account.communities import Communities
from cutecoin.models.account.wallets import Wallets
from cutecoin.models.node import Node

from PyQt5.QtWidgets import QDialog, QErrorMessage, QInputDialog

import gnupg


class Step():
    def __init__(self, config_dialog, previous_step=None, next_step=None):
        self.previous_step = previous_step
        self.next_step = next_step
        self.config_dialog = config_dialog


class StepPageInit(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        return True

    def process_next(self):
        pass

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)


class StepPageCommunities(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        return True

    def process_next(self):
        '''
        We create the community
        '''
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        default_node = Node.create(server, port, trust=True, hoster=True)
        account = self.config_dialog.account
        self.config_dialog.community = account.communities.add_community(
            default_node)
        #TODO: Get existing Wallet from ucoin node
        account.wallets.add_wallet(account.keyid,
                                   self.config_dialog.community)

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText("Ok")
        list_model = CommunitiesListModel(self.config_dialog.account)
        self.config_dialog.list_communities.setModel(list_model)


class ProcessConfigureAccount(QDialog, Ui_AccountConfigurationDialog):
    '''
    classdocs
    '''

    def __init__(self, core, account):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super(ProcessConfigureAccount, self).__init__()
        self.setupUi(self)
        self.account = account
        self.core = core
        step_init = StepPageInit(self)
        step_communities = StepPageCommunities(self)
        step_init.next_step = step_communities
        self.step = step_init
        self.step.display_page()
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
                Communities.create(),
                Wallets.create())
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
        dialog.accepted.connect(self.action_add_community)
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
        community = self.account.communities[index.row()]
        dialog = ProcessConfigureCommunity(self.account, community)
        dialog.accepted.connect(self.action_edit_community)
        dialog.exec_()

    def key_changed(self, key_index):
        gpg = gnupg.GPG()
        available_keys = gpg.list_keys(True)
        self.account.keyid = available_keys[key_index]['keyid']

    def next(self):
        if self.step.next_step is not None:
            if self.step.is_valid():
                self.step.process_next()
                self.step = self.step.next_step
                next_index = self.stacked_pages.currentIndex() + 1
                self.stacked_pages.setCurrentIndex(next_index)
                self.step.display_page()
        else:
            self.accept()

    def previous(self):
        if self.step.previous_step is not None:
            self.step = self.step.previous_step
            previous_index = self.stacked_pages.currentIndex() - 1
            self.stacked_pages.setCurrentIndex(previous_index)
            self.step.display_page()

    def accept(self):
        if self.account not in self.core.accounts:
            self.account.name = self.edit_account_name.text()
            try:
                self.core.add_account(self.account)
            except KeyAlreadyUsed as e:
                QErrorMessage(self).showMessage(e.message)
        self.accepted.emit()
        self.close()
