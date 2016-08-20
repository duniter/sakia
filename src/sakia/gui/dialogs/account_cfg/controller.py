from sakia.gui.component.controller import ComponentController
from .view import AccountConfigView
from .model import AccountConfigModel


class AccountConfigController(ComponentController):
    """
    The AccountConfigController view
    """

    def __init__(self, parent, view, model):
        """
        Constructor of the AccountConfigController component

        :param sakia.gui.AccountConfigController.view.AccountConfigControllerView: the view
        :param sakia.gui.AccountConfigController.model.AccountConfigControllerModel model: the model
        """
        super().__init__(parent, view, model)

        self.handle_next_step(init=True)
        self.view.button_next.clicked.connect(lambda checked: self.handle_next_step(False))
        self._steps = (
            {
                'page': self.view.page_init,
                'init': self.init_name_page,
                'next': self.account_name_selected
            },
            {
                'page': self.view.page_brainwallet,
                'init': self.init_key_page,
                'next': self.account_key_selected
            },
            {
                'page': self.view.page__communities,
                'init': self.inir_communities,
                'next': self.accept
            }
        )
        self._current_step = 0

    @classmethod
    def create(cls, parent, app, **kwargs):
        """
        Instanciate a AccountConfigController component
        :param sakia.gui.component.controller.ComponentController parent:
        :param sakia.core.Application app:
        :return: a new AccountConfigController controller
        :rtype: AccountConfigControllerController
        """
        view = AccountConfigView(parent.view)
        model = AccountConfigModel(None, app)
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

    def handle_next_step(self, init=False):
        if self._current_step < len(self._steps) - 1:
            if not init:
                self.view.button_next.clicked.disconnect(self._steps[self._current_step]['next'])
                self._current_step += 1
            self._steps[self._current_step]['init']()
            self.view.stackedWidget.setCurrentWidget(self._steps[self._current_step]['page'])
            self.view.button_next.clicked.connect(self._steps[self._current_step]['next'])

    @property
    def view(self) -> AccountConfigView:
        return self._view

    @property
    def model(self) -> AccountConfigModel:
        return self._model