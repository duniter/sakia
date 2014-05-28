'''
Created on 6 mars 2014

@author: inso
'''
from cutecoin.gen_resources.accountConfigurationDialog_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.generateAccountKeyDialog import GenerateAccountKeyDialog
from cutecoin.gui.processConfigureCommunity import ProcessConfigureCommunity
from cutecoin.models.account.communities.listModel import CommunitiesListModel
from cutecoin.tools.exceptions import KeyAlreadyUsed, Error
from cutecoin.models.node import Node

from PyQt5.QtWidgets import QDialog, QErrorMessage, QFileDialog, QMessageBox


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
        if self.config_dialog.account is None:
            name = self.config_dialog.edit_account_name.text()
            self.config_dialog.account = self.config_dialog.core.create_account(name)
        else:
            name = self.config_dialog.edit_account_name.text()
            self.config_dialog.account.name = name

    def display_page(self):
        if self.config_dialog.account is not None:
            self.config_dialog.edit_account_name.setText(self.config_dialog.account.name)
            model = CommunitiesListModel(self.config_dialog.account)
            self.config_dialog.list_communities.setModel(model)

        self.config_dialog.button_previous.setEnabled(False)


class StepPageGPG(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        return self.config_dialog.account.keyid != ''

    def process_next(self):
        model = CommunitiesListModel(self.config_dialog.account)
        self.config_dialog.list_communities.setModel(model)

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setEnabled(False)


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
        self.config_dialog.refresh()

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
        step_gpg = StepPageGPG(self)
        step_communities = StepPageCommunities(self)
        step_init.next_step = step_gpg
        step_gpg.next_step = step_communities
        self.step = step_init
        self.step.display_page()
        if self.account is None:
            self.setWindowTitle("New account")
        else:
            self.stacked_pages.removeWidget(self.stacked_pages.widget(1))
            step_init.next_step = step_communities
            self.setWindowTitle("Configure " + self.account.name)

    def open_process_add_community(self):
        dialog = ProcessConfigureCommunity(self.account, None)
        dialog.accepted.connect(self.action_add_community)
        dialog.exec_()

    def action_add_community(self):
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

    def open_generate_account_key(self):
        dialog = GenerateAccountKeyDialog(self.account, self)
        dialog.exec_()

    def open_import_key(self):
        keyfile = QFileDialog.getOpenFileName(self,
                                              "Choose a secret key",
                                              "",
                                              "All key files (*.asc);; Any file (*)")
        keyfile = keyfile[0]
        key = open(keyfile).read()
        result = self.account.gpg.import_keys(key)
        if result.count == 0:
            QErrorMessage(self).showMessage("Bad key file")
        else:
            QMessageBox.information(self, "Key import", "Key " +
                                    result.fingerprints[0] + " has been imported",
                            QMessageBox.Ok)
            if self.account.keyid is not '':
                self.account.gpg.delete_keys(self.account.keyid)

            secret_keys = self.account.gpg.list_keys(True)
            for k in secret_keys:
                if k['fingerprint'] == result.fingerprints[0]:
                    self.account.keyid = k['keyid']

            self.label_fingerprint.setText("Key : " + result.fingerprints[0])
            self.edit_secretkey_path.setText(keyfile)
            self.button_next.setEnabled(True)

    def next(self):
        if self.step.next_step is not None:
            if self.step.is_valid():
                try:
                    self.step.process_next()
                    self.step = self.step.next_step
                    next_index = self.stacked_pages.currentIndex() + 1
                    self.stacked_pages.setCurrentIndex(next_index)
                    self.step.display_page()
                except Error as e:
                    QErrorMessage(self).showMessage(e.message)

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
        self.core.save(self.account)
        self.accepted.emit()
        self.close()
