from PyQt5.QtWidgets import QDialog

from sakia.gui.password_asker import PasswordAskerDialog, detect_non_printable
from sakia.gui.component.controller import ComponentController
from ..community_cfg.controller import CommunityConfigController
from .view import AccountConfigView
from .model import AccountConfigModel
from sakia.tools.decorators import asyncify

import logging


class AccountConfigController(ComponentController):
    """
    The AccountConfigController view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the AccountConfigController component

        :param sakia.gui.account_cfg.view.AccountConfigCView: the view
        :param sakia.gui.account_cfg.model.AccountConfigModel model: the model
        """
        super().__init__(parent, view, model)

        self._current_step = 0
        self.view.button_next.clicked.connect(lambda checked: self.handle_next_step(False))
        self._steps = (
            {
                'page': self.view.page_init,
                'init': self.init_name_page,
                'check': self.check_name,
                'next': self.account_name_selected
            },
            {
                'page': self.view.page_brainwallet,
                'init': self.init_key_page,
                'check': self.check_key,
                'next': self.account_key_selected
            },
            {
                'page': self.view.page_communities,
                'init': self.init_communities,
                'check': lambda: True,
                'next': self.accept
            }
        )
        self.handle_next_step(init=True)
        self.password_asker = None
        self.view.values_changed.connect(self.check_values)

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a AccountConfigController component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new AccountConfigController controller
        :rtype: AccountConfigController
        """
        view = AccountConfigView(parent.view)
        model = AccountConfigModel(None, app, None)
        account_cfg = cls(parent, view, model)
        model.setParent(account_cfg)
        return account_cfg

    @classmethod
    def create_account(cls, parent, app):
        """
        Open a dialog to create a new account
        :param parent:
        :param app:
        :param account:
        :return:
        """
        account_cfg = cls.create(parent, app, account=None)
        account_cfg.view.set_creation_layout()
        account_cfg.view.exec()

    @classmethod
    def modify_account(cls, parent, app, account):
        """
        Open a dialog to modify an existing account
        :param parent:
        :param app:
        :param account:
        :return:
        """
        account_cfg = cls.create(parent, app, account=account)
        account_cfg.view.set_modification_layout(account.name)
        account_cfg._current_step = 1

    def check_values(self):
        """
        Check the values in the page and enable or disable previous/next buttons
        """
        valid = self._steps[self._current_step]['check']()
        self.view.button_next.setEnabled(valid)

    def init_name_page(self):
        """
        Initialize an account name page
        """
        if self.model.account:
            self.view.set_account_name(self.model.account.name)

        self.view.button_previous.setEnabled(False)
        self.view.button_next.setEnabled(False)

    def account_name_selected(self):
        name = self.view.account_name()
        if self.model.account is None:
            self.model.instanciate_account(name)
        else:
            self.model.rename_account(name)

    def check_name(self):
        return len(self.view.edit_account_name.text()) > 2

    def init_key_page(self):
        """
        Initialize key page
        """
        self.view.button_previous.setEnabled(False)
        self.view.button_next.setEnabled(False)

    def account_key_selected(self):
        salt = self.view.edit_salt.text()
        password = self.view.edit_password.text()
        self.model.account.set_scrypt_infos(salt, password)
        self.password_asker = PasswordAskerDialog(self.model.account)

    def check_key(self):
        if self.model.app.preferences['expert_mode']:
            return True

        if len(self.view.edit_salt.text()) < 6:
            self.view.label_info.setText(self.tr("Forbidden : salt is too short"))
            return False

        if len(self.view.edit_password.text()) < 6:
            self.view.label_info.setText(self.tr("Forbidden : password is too short"))
            return False

        if detect_non_printable(self.view.edit_salt.text()):
            self.view.label_info.setText(self.tr("Forbidden : Invalid characters in salt field"))
            return False

        if detect_non_printable(self.view.edit_password.text()):
            self.view.label_info.setText(
                self.tr("Forbidden : Invalid characters in password field"))
            return False

        if self.view.edit_password.text() != \
                self.view.edit_password_repeat.text():
            self.view.label_info.setText(self.tr("Error : passwords are different"))
            return False

        self.view.label_info.setText("")
        return True

    def init_communities(self):
        self.view.button_add_community.clicked.connect(self.open_process_add_community)
        self.view.button_previous.setEnabled(False)
        self.view.button_next.setText("Ok")
        list_model = self.model.communities_list_model()
        self.view.set_communities_list_model(list_model)

    def handle_next_step(self, init=False):
        if self._current_step < len(self._steps) - 1:
            if not init:
                self._steps[self._current_step]['next']()
                self._current_step += 1
            self._steps[self._current_step]['init']()
            self.view.stacked_pages.setCurrentWidget(self._steps[self._current_step]['page'])

    @asyncify
    async def open_process_add_community(self, checked=False):
        logging.debug("Opening configure community dialog")
        logging.debug(self.password_asker)
        await CommunityConfigController.create_community(self,
                                                         self.model.app,
                                                         account=self.model.account,
                                                         password_asker=self.password_asker)


    def accept(self):
        if self.password_asker.result() == QDialog.Rejected:
            return
        self.model.add_account_to_app()
        self.view.accept()

    @property
    def view(self) -> AccountConfigView:
        return self._view

    @property
    def model(self) -> AccountConfigModel:
        return self._model