"""
Created on 6 mars 2014

@author: inso
"""
import logging
import asyncio
from ucoinpy.key import SigningKey
from ..gen_resources.account_cfg_uic import Ui_AccountConfigurationDialog
from ..gui.process_cfg_community import ProcessConfigureCommunity
from ..gui.password_asker import PasswordAskerDialog, detect_non_printable
from ..gui.widgets.dialogs import QAsyncMessageBox
from ..models.communities import CommunitiesListModel
from ..tools.exceptions import KeyAlreadyUsed, Error, NoPeerAvailable
from ..tools.decorators import asyncify

from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QRegExpValidator


class Step():
    def __init__(self, config_dialog, previous_step=None, next_step=None):
        self.previous_step = previous_step
        self.next_step = next_step
        self.config_dialog = config_dialog


class StepPageInit(Step):
    """
    First step when adding a community
    """

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
            self.config_dialog.password_asker = PasswordAskerDialog(self.config_dialog.account)

        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setEnabled(False)


class StepPageKey(Step):
    """
    First step when adding a community
    """

    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        if len(self.config_dialog.edit_salt.text()) < 6:
            self.config_dialog.label_info.setText(self.config_dialog.tr("Forbidden : salt is too short"))
            return False

        if len(self.config_dialog.edit_password.text()) < 6:
            self.config_dialog.label_info.setText(self.config_dialog.tr("Forbidden : password is too short"))
            return False

        if detect_non_printable(self.config_dialog.edit_salt.text()):
            self.config_dialog.label_info.setText(self.config_dialog.tr("Forbidden : Invalid characters in salt field"))
            return False

        if detect_non_printable(self.config_dialog.edit_password.text()):
            self.config_dialog.label_info.setText(
                self.config_dialog.tr("Forbidden : Invalid characters in password field"))
            return False

        if self.config_dialog.edit_password.text() != \
                self.config_dialog.edit_password_repeat.text():
            self.config_dialog.label_info.setText(self.config_dialog.tr("Error : passwords are different"))
            return False

        self.config_dialog.label_info.setText("")
        return True

    def process_next(self):
        salt = self.config_dialog.edit_salt.text()
        password = self.config_dialog.edit_password.text()
        self.config_dialog.account.set_scrypt_infos(salt, password)
        self.config_dialog.password_asker = PasswordAskerDialog(self.config_dialog.account)
        model = CommunitiesListModel(self.config_dialog.account)
        self.config_dialog.list_communities.setModel(model)

    def display_page(self):
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setEnabled(False)


class StepPageCommunities(Step):
    """
    First step when adding a community
    """

    def __init__(self, config_dialog):
        super().__init__(config_dialog)

    def is_valid(self):
        return True

    def process_next(self):
        password = self.config_dialog.password_asker.exec_()
        if self.config_dialog.password_asker.result() == QDialog.Rejected:
            return

        self.config_dialog.app.add_account(self.config_dialog.account)
        if len(self.config_dialog.app.accounts) == 1:
            self.config_dialog.app.preferences['account'] = self.config_dialog.account.name
        self.config_dialog.app.save(self.config_dialog.account)
        self.config_dialog.app.change_current_account(self.config_dialog.account)

    def display_page(self):
        logging.debug("Communities DISPLAY")
        self.config_dialog.button_previous.setEnabled(False)
        self.config_dialog.button_next.setText("Ok")
        list_model = CommunitiesListModel(self.config_dialog.account)
        self.config_dialog.list_communities.setModel(list_model)


class ProcessConfigureAccount(QDialog, Ui_AccountConfigurationDialog):
    """
    classdocs
    """

    def __init__(self, app, account):
        """
        Constructor
        """
        # Set up the user interface from Designer.
        super().__init__()
        self.setupUi(self)
        regexp = QRegExp('[A-Za-z0-9_-]*')
        validator = QRegExpValidator(regexp)
        self.edit_account_name.setValidator(validator)
        self.account = account
        self.password_asker = None
        self.app = app
        step_init = StepPageInit(self)
        step_key = StepPageKey(self)
        step_communities = StepPageCommunities(self)
        step_init.next_step = step_key
        step_key.next_step = step_communities
        self.step = step_init
        self.step.display_page()
        if self.account is None:
            self.setWindowTitle(self.tr("New account"))
            self.button_delete.hide()
        else:
            self.stacked_pages.removeWidget(self.stacked_pages.widget(1))
            step_init.next_step = step_communities
            self.button_next.setEnabled(True)
            self.stacked_pages.currentWidget()
            self.setWindowTitle(self.tr("Configure {0}".format(self.account.name)))

    def open_process_add_community(self):
        logging.debug("Opening configure community dialog")
        logging.debug(self.password_asker)
        dialog = ProcessConfigureCommunity(self.app,
                                           self.account, None,
                                           self.password_asker)
        dialog.accepted.connect(self.action_add_community)
        dialog.exec_()

    def action_add_community(self):
        logging.debug("Action add community : done")
        self.list_communities.setModel(CommunitiesListModel(self.account))
        self.button_next.setEnabled(True)
        self.button_next.setText(self.tr("Ok"))

    def action_remove_community(self):
        for index in self.list_communities.selectedIndexes():
            self.account.communities.pop(index.row())

        self.list_communities.setModel(CommunitiesListModel(self.account))

    def action_edit_community(self):
        self.list_communities.setModel(CommunitiesListModel(self.account))

    def action_edit_account_key(self):
        self.button_generate.setEnabled(self.step.is_valid())
        self.button_next.setEnabled(self.step.is_valid())

    def action_show_pubkey(self):
        salt = self.edit_salt.text()
        password = self.edit_password.text()
        pubkey = SigningKey(salt, password).pubkey
        self.label_info.setText(pubkey)

    def action_edit_account_parameters(self):
        if self.step.is_valid():
            self.button_next.setEnabled(True)
        else:
            self.button_next.setEnabled(False)

    def open_process_edit_community(self, index):
        community = self.account.communities[index.row()]
        dialog = ProcessConfigureCommunity(self.app, self.account, community, self.password_asker)

        dialog.accepted.connect(self.action_edit_community)
        dialog.exec_()

    @asyncify
    async def action_delete_account(self):
        reply = await QAsyncMessageBox.question(self, self.tr("Warning"),
                                     self.tr("""This action will delete your account locally.
Please note your key parameters (salt and password) if you wish to recover it later.
Your account won't be removed from the networks it joined.
Are you sure ?"""))
        if reply == QMessageBox.Yes:
            account = self.app.current_account
            await self.app.delete_account(account)
            self.app.save(account)
            self.accept()

    def next(self):
        if self.step.is_valid():
            try:
                self.step.process_next()
                if self.step.next_step is not None:
                    self.step = self.step.next_step
                    next_index = self.stacked_pages.currentIndex() + 1
                    self.stacked_pages.setCurrentIndex(next_index)
                    self.step.display_page()
                else:
                    self.accept()
            except Error as e:
                QMessageBox.critical(self, self.tr("Error"),
                                     str(e), QMessageBox.Ok)

    def previous(self):
        if self.step.previous_step is not None:
            self.step = self.step.previous_step
            previous_index = self.stacked_pages.currentIndex() - 1
            self.stacked_pages.setCurrentIndex(previous_index)
            self.step.display_page()

    def async_exec(self):
        future = asyncio.Future()
        self.finished.connect(lambda r: future.set_result(r))
        self.open()
        return future

    def accept(self):
        super().accept()
