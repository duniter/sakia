'''
Created on 6 mars 2014

@author: inso
'''
import logging
from ucoinpy.documents.peer import Peer
from ucoinpy.key import SigningKey
from cutecoin.gen_resources.account_cfg_uic import Ui_AccountConfigurationDialog
from cutecoin.gui.process_cfg_community import ProcessConfigureCommunity
from cutecoin.models.communities import CommunitiesListModel
from cutecoin.tools.exceptions import KeyAlreadyUsed, Error

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
        if len(self.config_dialog.edit_account_name.text()) > 2:
            return True
        else:
            return False

    def process_next(self):
        if self.config_dialog.account is None:
            name = self.config_dialog.edit_account_name.text()
            self.config_dialog.account = self.config_dialog.app.create_account(name)
        else:
            name = self.config_dialog.edit_account_name.text()
            self.config_dialog.account.name = name

    def display_page(self):
        if self.config_dialog.account is not None:
            self.config_dialog.edit_account_name.setText(self.config_dialog.account.name)
            model = CommunitiesListModel(self.config_dialog.account)
            self.config_dialog.list_communities.setModel(model)

        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setEnabled(False)


class StepPageKey(Step):
    '''
    First step when adding a community
    '''
    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        if len(self.config_dialog.edit_password.text()) < 2:
            return False

        if len(self.config_dialog.edit_email.text()) < 2:
            return False

        if len(self.config_dialog.edit_password.text()) < 6:
            self.config_dialog.label_info.setText("Warning : password is too short")

        if self.config_dialog.edit_password.text() != \
            self.config_dialog.edit_password_repeat.text():
            self.config_dialog.label_info.setText("Error : passwords are different")
            return False

        self.config_dialog.label_info.setText("")
        return True

    def process_next(self):
        salt = self.config_dialog.edit_email.text()
        password = self.config_dialog.edit_password.text()
        self.config_dialog.account.salt = salt
        self.config_dialog.account.pubkey = SigningKey(salt, password).pubkey
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
        logging.debug("Communities NEXT ")
        server = self.config_dialog.lineedit_server.text()
        port = self.config_dialog.spinbox_port.value()
        account = self.config_dialog.account
        self.config_dialog.community = account.add_community(server, port)
        account.wallets.add_wallet(0,
                                   self.config_dialog.community)
        self.config_dialog.refresh()

    def display_page(self):
        logging.debug("Communities DISPLAY")
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText("Ok")
        list_model = CommunitiesListModel(self.config_dialog.account)
        self.config_dialog.list_communities.setModel(list_model)


class ProcessConfigureAccount(QDialog, Ui_AccountConfigurationDialog):
    '''
    classdocs
    '''

    def __init__(self, app, account):
        '''
        Constructor
        '''
        # Set up the user interface from Designer.
        super().__init__()
        self.setupUi(self)
        self.account = account
        self.app = app
        step_init = StepPageInit(self)
        step_key = StepPageKey(self)
        step_communities = StepPageCommunities(self)
        step_init.next_step = step_key
        step_key.next_step = step_communities
        self.step = step_init
        self.step.display_page()
        if self.account is None:
            self.setWindowTitle("New account")
        else:
            self.stacked_pages.removeWidget(self.stacked_pages.widget(1))
            step_init.next_step = step_communities
            self.setWindowTitle("Configure " + self.account.name)

    def open_process_add_community(self):
        logging.debug("Opening configure community dialog")
        dialog = ProcessConfigureCommunity(self.account, None)
        dialog.accepted.connect(self.action_add_community)
        dialog.exec_()

    def action_add_community(self):
        logging.debug("Action add community : done")
        self.list_communities.setModel(CommunitiesListModel(self.account))
        self.button_next.setEnabled(True)
        self.button_next.setText("Ok")

    def action_remove_community(self):
        for index in self.list_communities.selectedIndexes():
            community = self.account.communities.communitiesList[index.row()]
            self.account.wallets.removeAllWalletsOf(community)
            self.account.communities.communitiesList.pop(index.row())

        self.list_communities.setModel(CommunitiesListModel(self.account))

    def action_edit_community(self):
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def action_edit_account_key(self):
        if self.step.is_valid():
            self.button_next.setEnabled(True)
        else:
            self.button_next.setEnabled(False)

    def action_show_pubkey(self):
        salt = self.edit_email.text()
        password = self.edit_password.text()
        pubkey = SigningKey(salt, password).pubkey
        QMessageBox.information(self, "Public key", "These parameters pubkeys are : {0}".format(pubkey))

    def action_edit_account_name(self):
        if self.step.is_valid():
            self.button_next.setEnabled(True)
        else:
            self.button_next.setEnabled(False)

    def open_process_edit_community(self, index):
        community = self.account.communities[index.row()]
        dialog = ProcessConfigureCommunity(self.account, community)
        dialog.accepted.connect(self.action_edit_community)
        dialog.exec_()

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
        if self.account not in self.app.accounts:
            self.account.name = self.edit_account_name.text()
            try:
                self.app.add_account(self.account)
            except KeyAlreadyUsed as e:
                QErrorMessage(self).showMessage(e.message)
        self.app.save(self.account)
        self.accepted.emit()
        self.close()
