from sakia.gui.component.model import ComponentModel
from sakia.models.communities import CommunitiesListModel

class AccountConfigModel(ComponentModel):
    """
    The model of AccountConfig component
    """

    def __init__(self, parent, app, account):
        """

        :param sakia.gui.dialogs.account_cfg.controller.AccountConfigController parent:
        :param sakia.core.Application app:
        :param sakia.core.Account account:
        """
        super().__init__(parent)
        self.app = app
        self.account = account

    def instanciate_account(self, name):
        """
        Creates an account with a given name
        :param str name: the name of the new account
        """
        self.account = self.app.create_account(name)

    def rename_account(self, name):
        """
        Renames current account
        :param str name: the new name
        """
        self.account.name = name

    def communities_list_model(self):
        return CommunitiesListModel(self.account)

    def add_account_to_app(self):
        self.app.add_account(self.account)
        if len(self.app.accounts) == 1:
            self.app.preferences['account'] = self.account.name
        self.app.save(self.account)
        self.app.change_current_account(self.account)